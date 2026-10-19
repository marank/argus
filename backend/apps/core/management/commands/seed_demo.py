"""Fill an empty development database with realistic demo data.

Demo accounts (development only):

    admin    / argus-demo   superuser
    it       / argus-demo   IT department
    employee / argus-demo   regular employee
    sales    / argus-demo   regular employee
    terminal / argus-demo   shared pickup terminal
"""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Department, User
from apps.core.models import NumberSequence
from apps.core.services.numbering import get_sequence
from apps.inventory.models import Asset, AssetEvent, StockItem, StockMovement
from apps.inventory.services import assets as asset_service
from apps.inventory.services.stock import move_stock
from apps.masterdata.models import AssetModel, Category, Location, Manufacturer, Supplier
from apps.reservations.services import workflow

DEMO_PASSWORD = "argus-demo"

CATEGORIES = [
    # code, name, icon, prefix, parent
    ("laptops", "Laptops", "laptop", "LT-", None),
    ("workstations", "Workstations", "desktop", "WS-", None),
    ("phones", "Smartphones", "mobile", "PH-", None),
    ("headsets", "Headsets", "headphones", "HS-", None),
    ("input", "Mouse & keyboard", "keyboard", "IN-", None),
    ("mde", "Mobile data terminals", "barcode", "MDE-", None),
    ("mde-accessories", "MDE accessories", "plug", "MDA-", "mde"),
    ("consumables", "Consumables", "box", None, None),
]

MODELS = [
    # manufacturer, name, category, tracking, ean, price
    ("Lenovo", "ThinkPad T14 Gen 5", "laptops", "serialized", "0197532123456", "1349.00"),
    ("Apple", "MacBook Air 13 M4", "laptops", "serialized", "0195949123457", "1299.00"),
    ("Dell", "Precision 3680 Tower", "workstations", "serialized", "5397184123458", "1890.00"),
    ("Apple", "iPhone 16", "phones", "serialized", "0195949123459", "899.00"),
    ("Samsung", "Galaxy A56", "phones", "serialized", "8806095123450", "449.00"),
    ("Jabra", "Evolve2 65", "headsets", "serialized", "5706991123451", "219.00"),
    ("Jabra", "Evolve2 40 SE", "headsets", "serialized", "5706991123452", "99.00"),
    ("Logitech", "MX Keys S Combo", "input", "serialized", "5099206123453", "189.00"),
    ("Scanova", "SX58", "mde", "serialized", "5711045123454", "1450.00"),
    ("Scanova", "SX5x Trigger Handle", "mde-accessories", "serialized", "5711045123455", "79.00"),
    (
        "Scanova",
        "SX5x 5-Slot Charging Cradle",
        "mde-accessories",
        "serialized",
        "5711045123456",
        "399.00",
    ),
    ("Scanova", "SX5x Battery 4680 mAh", "mde-accessories", "bulk", "5711045123457", "69.00"),
    ("HP", "305 black ink cartridge", "consumables", "bulk", "0190780123458", "14.90"),
    ("HP", "305 tri-colour ink cartridge", "consumables", "bulk", "0190780123459", "16.90"),
]


class Command(BaseCommand):
    help = "Create demo data for local development."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Seed even if data exists.")

    @transaction.atomic
    def handle(self, *args, force: bool = False, **options):
        if Asset.objects.exists() and not force:
            raise CommandError("The database already contains assets. Use --force to seed anyway.")

        for code in ("asset", "reservation", "purchase-order"):
            get_sequence(code)

        departments = {
            name: Department.objects.get_or_create(name=name, defaults={"code": code})[0]
            for name, code in [
                ("IT", "IT"),
                ("Logistics", "LOG"),
                ("Sales", "SAL"),
                ("Accounting", "ACC"),
            ]
        }
        admin = self._user("admin", "Ada", "Admin", departments["IT"], staff=True, superuser=True)
        it = self._user("it", "Ian", "Tech", departments["IT"], staff=True)
        employee = self._user("employee", "Erika", "Muster", departments["Logistics"])
        sales = self._user("sales", "Sam", "Seller", departments["Sales"])
        terminal = self._user("terminal", "Pickup", "Terminal", departments["IT"])
        terminal.is_terminal = True
        terminal.save()

        hq = Location.objects.create(name="Headquarters", code="HQ", kind=Location.Kind.SITE)
        storage = Location.objects.create(
            name="IT storage", code="HQ-IT-01", kind=Location.Kind.STORAGE, parent=hq
        )
        Location.objects.create(
            name="IT service desk",
            code="HQ-IT-00",
            kind=Location.Kind.ROOM,
            parent=hq,
            is_pickup_point=True,
        )
        warehouse = Location.objects.create(
            name="Warehouse", code="WH", kind=Location.Kind.BUILDING, parent=hq
        )

        supplier = Supplier.objects.create(
            name="Nordlicht IT AG", customer_number="K-104233", email="orders@example.com"
        )
        Supplier.objects.create(name="Scanova Partner GmbH", customer_number="Z-5521")

        categories: dict[str, Category] = {}
        for index, (code, name, icon, prefix, parent) in enumerate(CATEGORIES):
            sequence = None
            if prefix:
                sequence = NumberSequence.objects.create(
                    code=f"category-{code}",
                    name=name,
                    prefix=prefix,
                    pattern="{prefix}{seq}",
                    padding=4,
                )
            categories[code] = Category.objects.create(
                allow_any_model=code not in ("mde-accessories", "consumables"),
                code=code,
                name=name,
                icon=icon,
                number_sequence=sequence,
                parent=categories.get(parent),
                sort_order=index * 10,
            )

        models: dict[str, AssetModel] = {}
        for maker, name, category, tracking, ean, price in MODELS:
            manufacturer, _ = Manufacturer.objects.get_or_create(name=maker)
            models[name] = AssetModel.objects.create(
                manufacturer=manufacturer,
                name=name,
                category=categories[category],
                tracking=tracking,
                ean=ean,
                list_price=price,
                default_supplier=supplier,
            )
        models["SX58"].compatible_with.set(
            [
                models[n]
                for n in (
                    "SX5x Trigger Handle",
                    "SX5x 5-Slot Charging Cradle",
                    "SX5x Battery 4680 mAh",
                )
            ]
        )

        today = timezone.localdate()
        serial_counts = {
            "ThinkPad T14 Gen 5": 8,
            "MacBook Air 13 M4": 3,
            "Precision 3680 Tower": 2,
            "iPhone 16": 4,
            "Galaxy A56": 4,
            "Evolve2 65": 6,
            "Evolve2 40 SE": 10,
            "MX Keys S Combo": 6,
            "SX58": 6,
            "SX5x Trigger Handle": 6,
            "SX5x 5-Slot Charging Cradle": 2,
        }
        created: dict[str, list[Asset]] = {}
        for model_index, (name, count) in enumerate(serial_counts.items(), start=1):
            model = models[name]
            created[name] = [
                asset_service.create_asset(
                    {
                        "model": model.pk,
                        "serial_number": f"{model.manufacturer.name[:2].upper()}{model_index:03d}{i:04d}",
                        "location": storage.pk,
                        "supplier": supplier.pk,
                        "purchase_date": today - timedelta(days=30 * i + 40),
                        "purchase_price": model.list_price,
                        "warranty_until": today + timedelta(days=700 - 90 * i),
                        "condition": Asset.Condition.GOOD if i % 3 else Asset.Condition.NEW,
                    },
                    admin,
                )
                for i in range(count)
            ]

        # A few devices permanently in use and some history.
        asset_service.update_asset(created["ThinkPad T14 Gen 5"][0], {"assigned_to": employee.pk}, it)
        asset_service.update_asset(created["iPhone 16"][0], {"assigned_to": employee.pk}, it)
        for mde in created["SX58"][:3]:
            asset_service.record_event(
                mde,
                {
                    "kind": AssetEvent.Kind.BATTERY_REPLACED,
                    "description": "Battery no longer held a full shift.",
                    "component": "Battery 4680 mAh",
                    "occurred_at": timezone.now() - timedelta(days=12),
                },
                it,
            )

        for name, quantity, minimum in [
            ("HP 305 black ink cartridge", 4, 10),
            ("HP 305 tri-colour ink cartridge", 12, 6),
            ("SX5x Battery 4680 mAh", 8, 4),
        ]:
            model = AssetModel.objects.get(name=name.removeprefix("HP "))
            stock = StockItem.objects.create(
                model=model,
                location=warehouse if "SX5x" in name else storage,
                min_quantity=minimum,
            )
            move_stock(stock, quantity, StockMovement.Reason.RECEIPT, admin, note="Initial stock")

        workflow.submit(
            employee,
            {
                "title": "Inventory count in the warehouse",
                "duration": "temporary",
                "start_date": today + timedelta(days=5),
                "end_date": today + timedelta(days=9),
                "notes": "Needed for the annual stocktaking.",
            },
            [
                {"asset_model": models["SX58"].pk, "quantity": 3},
                {"asset_model": models["SX5x Trigger Handle"].pk, "quantity": 3},
                {"asset_model": models["SX5x 5-Slot Charging Cradle"].pk, "quantity": 2},
            ],
            created_by=employee,
        )
        workflow.submit(
            employee,
            {"title": "New headset", "duration": "permanent", "start_date": today},
            [{"category": categories["headsets"].pk, "quantity": 1, "note": "Wireless preferred"}],
            created_by=employee,
        )
        workshop = workflow.submit(
            employee,
            {
                "title": "Training workshop",
                "duration": "temporary",
                "start_date": today + timedelta(days=2),
                "end_date": today + timedelta(days=4),
            },
            [{"category": categories["laptops"].pk, "quantity": 4}],
            created_by=employee,
        )
        workflow.approve(workshop, it, {}, timezone.now() + timedelta(days=2), None, "Pick up at the desk.")

        # One prepared pickup waiting at the terminal.
        onboarding = workflow.submit(
            sales,
            {"title": "Onboarding new sales rep", "duration": "permanent", "start_date": today},
            [
                {"category": categories["laptops"].pk, "quantity": 1},
                {"category": categories["headsets"].pk, "quantity": 1},
                {"asset_model": models["MX Keys S Combo"].pk, "quantity": 1},
            ],
            created_by=sales,
        )
        workflow.approve(onboarding, it, {}, timezone.now() + timedelta(hours=2), None, "")
        workflow.auto_allocate(onboarding, it)
        workflow.mark_ready(onboarding, it)

        self.stdout.write(self.style.SUCCESS(f"Demo data created. Password: {DEMO_PASSWORD}"))

    def _user(self, username, first, last, department, staff=False, superuser=False) -> User:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first,
                "last_name": last,
                "department": department,
                "email": f"{username}@example.com",
                "is_staff": staff,
                "is_superuser": superuser,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user
