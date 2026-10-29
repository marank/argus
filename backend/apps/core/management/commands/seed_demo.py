"""Fill an empty development database with realistic demo data.

Demo accounts (development only):

    admin    / argus-demo   superuser
    it       / argus-demo   IT department
    employee / argus-demo   regular employee
    sales    / argus-demo   regular employee
    terminal / argus-demo   shared pickup terminal
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Department, Role, Team, User
from apps.accounts.permissions import READ, RESOURCE_KEYS, WRITE
from apps.core.models import NumberSequence
from apps.core.services.numbering import get_sequence
from apps.inventory.models import (
    Asset,
    AssetEvent,
    AssetIssue,
    Consumable,
    ConsumableMovement,
    License,
)
from apps.inventory.services import assets as asset_service
from apps.inventory.services import issues as issue_service
from apps.inventory.services import licenses as license_service
from apps.inventory.services.consumables import move_consumable
from apps.masterdata.models import AssetModel, Category, Location, Manufacturer, Supplier
from apps.procurement.services import orders as order_service
from apps.requests.models import Handover
from apps.requests.services import workflow

DEMO_PASSWORD = "argus-demo"

CATEGORIES = [
    # code, name, icon, prefix, parent
    ("laptops", "Laptops", "laptop", "LT", None),
    ("workstations", "Workstations", "desktop", "WS", None),
    ("phones", "Smartphones", "mobile", "PH", None),
    ("headsets", "Headsets", "headphones", "HS", None),
    ("input", "Mouse & keyboard", "keyboard", "IN", None),
    ("mde", "Mobile data terminals", "barcode", "MDE", None),
    ("mde-accessories", "MDE accessories", "plug", "MDA", "mde"),
    ("printers", "Printers", "printer", "PR", None),
    ("consumables", "Consumables", "box", None, None),
    ("office-software", "Office & collaboration", "app", None, None),
    ("design-software", "Design & engineering", "app", None, None),
]
SOFTWARE_CATEGORIES = {"office-software", "design-software"}
# Singular names for "any model" requests, e.g. "Laptop · any model".
ITEM_NAMES = {
    "laptops": "Laptop",
    "workstations": "Workstation",
    "phones": "Smartphone",
    "headsets": "Headset",
    "input": "Mouse & keyboard set",
    "mde": "Mobile data terminal",
    "printers": "Printer",
}

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
    ("HP", "DeskJet 2820e", "printers", "serialized", "0196786123450", "79.00"),
    ("HP", "305 black ink cartridge", "consumables", "bulk", "0190780123458", "14.90"),
    ("HP", "305 tri-colour ink cartridge", "consumables", "bulk", "0190780123459", "16.90"),
    ("Microsoft", "365 Business Standard", "office-software", "license", "", "150.00"),
    ("Adobe", "Acrobat Pro", "office-software", "license", "", "239.88"),
    ("Autodesk", "AutoCAD LT", "design-software", "license", "", "540.00"),
]


class Command(BaseCommand):
    help = "Create demo data for local development."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Seed even if data exists.")

    @transaction.atomic
    def handle(self, *args, force: bool = False, **options):
        if Asset.objects.exists() and not force:
            raise CommandError("The database already contains assets. Use --force to seed anyway.")
        seed_extra(self.seed_base(), self.stdout)
        self.stdout.write(self.style.SUCCESS(f"Demo data created. Password: {DEMO_PASSWORD}"))

    def seed_base(self) -> dict:
        """The core set: demo accounts, catalog, devices and a few requests.

        The tests start from this part only, so they stay fast and their
        expectations (counts, seats) stable; the command adds ``seed_extra``."""

        for code in ("asset", "request", "purchase-order"):
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
        full_access = Role.objects.create(
            name="Full access",
            description="Read and change everything.",
            permissions=dict.fromkeys(RESOURCE_KEYS, WRITE),
        )
        full_access.members.add(it)

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
                    pattern="{prefix}-{seq}",
                    padding=4,
                )
            categories[code] = Category.objects.create(
                allow_any_model=code not in ("mde-accessories", "consumables", *SOFTWARE_CATEGORIES),
                kind=Category.Kind.SOFTWARE if code in SOFTWARE_CATEGORIES else Category.Kind.HARDWARE,
                code=code,
                name=name,
                item_name=ITEM_NAMES.get(code, ""),
                icon=icon,
                number_sequence=sequence,
                parent=categories[parent] if parent else None,
                sort_order=index * 10,
            )

        models: dict[str, AssetModel] = {}
        for maker, name, category, tracking, ean, price in MODELS:
            manufacturer, _ = Manufacturer.objects.get_or_create(name=maker)
            models[name] = AssetModel.objects.create(
                manufacturer=manufacturer,
                name=name,
                designation=name,
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

        models["DeskJet 2820e"].compatible_with.set(
            [models["305 black ink cartridge"], models["305 tri-colour ink cartridge"]]
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
            "DeskJet 2820e": 2,
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
        asset_service.update_asset(created["DeskJet 2820e"][0], {"assigned_to": employee.pk}, it)
        # Software licenses: per employee and per device, one expiring soon.
        m365 = License.objects.create(
            model=models["365 Business Standard"],
            reference="CSP subscription 2026",
            seats=25,
            valid_from=today - timedelta(days=165),
            valid_until=today + timedelta(days=200),
            supplier=supplier,
            purchase_price="3750.00",
        )
        acrobat = License.objects.create(
            model=models["Acrobat Pro"], reference="VIP contract", seats=5, supplier=supplier
        )
        autocad = License.objects.create(
            model=models["AutoCAD LT"],
            reference="Subscription",
            seats=2,
            assign_to=License.AssignTo.DEVICE,
            valid_until=today + timedelta(days=20),
            supplier=supplier,
        )
        for person in (employee, sales, admin, it):
            license_service.assign_license(m365, it, user_id=person.pk)
        license_service.assign_license(acrobat, it, user_id=sales.pk)
        license_service.assign_license(autocad, it, asset_id=created["Precision 3680 Tower"][0].pk)
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
            consumable = Consumable.objects.create(
                model=model,
                location=warehouse if "SX5x" in name else storage,
                min_quantity=minimum,
            )
            move_consumable(
                consumable, quantity, ConsumableMovement.Reason.RECEIPT, admin, note="Initial stock"
            )

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
        workflow.confirm(workshop, it, {}, "Pick up at the desk.")

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
        workflow.confirm(onboarding, it, {})
        workflow.auto_allocate(onboarding, it)
        workflow.mark_ready(onboarding, it, pickup_at=timezone.now() + timedelta(hours=2))

        return {
            "admin": admin,
            "it": it,
            "categories": categories,
            "models": models,
            "storage": storage,
            "warehouse": warehouse,
            "hq": hq,
            "supplier": supplier,
            "make_user": self._user,
        }

    def _user(self, username, first, last, department, staff=False, superuser=False) -> User:
        user, created = User.objects.get_or_create(
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
        # Existing accounts keep their password: on a real installation "admin" is the
        # administrator from ADMIN_USERNAME, not a demo account.
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user


EXTRA_DEPARTMENTS = [
    # name, code, cost center, sort order
    ("Management", "MGT", "1000", 10),
    ("IT", "IT", "1100", 20),
    ("Sales", "SAL", "2000", 30),
    ("Customer Service", "CS", "2100", 40),
    ("Marketing", "MKT", "2200", 50),
    ("Logistics", "LOG", "3000", 60),
    ("Purchasing", "PUR", "3100", 70),
    ("Accounting", "ACC", "4000", 80),
]

EXTRA_PEOPLE = [
    # username, first, last, department, job title
    ("jkoch", "Jonas", "Koch", "IT", "IT support"),
    ("lweber", "Lena", "Weber", "Management", "Managing director"),
    ("mschmidt", "Markus", "Schmidt", "Sales", "Key account manager"),
    ("abecker", "Anna", "Becker", "Sales", "Sales representative"),
    ("tfischer", "Tobias", "Fischer", "Sales", "Sales representative"),
    ("jwagner", "Julia", "Wagner", "Customer Service", "Team lead customer service"),
    ("dhoffmann", "David", "Hoffmann", "Customer Service", "Customer service agent"),
    ("sschulz", "Sophie", "Schulz", "Customer Service", "Customer service agent"),
    ("lneumann", "Lukas", "Neumann", "Marketing", "Marketing manager"),
    ("mbraun", "Marie", "Braun", "Marketing", "Content designer"),
    ("fzimmermann", "Felix", "Zimmermann", "Logistics", "Warehouse lead"),
    ("lkrueger", "Laura", "Krüger", "Logistics", "Warehouse clerk"),
    ("pwolf", "Paul", "Wolf", "Logistics", "Warehouse clerk"),
    ("ehartmann", "Emma", "Hartmann", "Logistics", "Dispatcher"),
    ("nlange", "Niklas", "Lange", "Purchasing", "Buyer"),
    ("hkrause", "Hannah", "Krause", "Purchasing", "Buyer"),
    ("bschmitt", "Ben", "Schmitt", "Accounting", "Accountant"),
    ("cmeyer", "Clara", "Meyer", "Accounting", "Payroll"),
    ("jwerner", "Jan", "Werner", "Sales", "Inside sales"),
    ("mrichter", "Mia", "Richter", "Marketing", "Trainee"),
]

EXTRA_CATEGORIES = [
    # code, name, icon, inventory prefix, parent, singular, kind
    ("tablets", "Tablets", "tablet", "TB", None, "Tablet", "hardware"),
    ("monitors", "Monitors", "desktop", "MO", None, "Monitor", "hardware"),
    ("laptop-accessories", "Laptop accessories", "plug", "LA", "laptops", "", "hardware"),
    ("operating-systems", "Operating systems", "shield", None, None, "", "software"),
]

EXTRA_MODELS = [
    # manufacturer, name, category, tracking, price, warranty months
    ("Lenovo", "ThinkPad X1 Carbon Gen 12", "laptops", "serialized", "1899.00", 36),
    ("Dell", "Latitude 5450", "laptops", "serialized", "1149.00", 36),
    ("Apple", "iPad 10.9 (10th gen)", "tablets", "serialized", "449.00", 12),
    ("Samsung", "Galaxy Tab S9 FE", "tablets", "serialized", "399.00", 24),
    ("Dell", "P2425H", "monitors", "serialized", "189.00", 36),
    ("LG", "27UP850", "monitors", "serialized", "449.00", 24),
    ("Lenovo", "ThinkPad Universal USB-C Dock", "laptop-accessories", "serialized", "229.00", 36),
    ("Logitech", "MX Master 3S", "input", "serialized", "109.00", 24),
    ("Brother", "HL-L2350DW", "printers", "serialized", "139.00", 24),
    ("Brother", "TN-2420 toner", "consumables", "bulk", "64.90", 0),
    ("Generic", "USB-C cable 2 m", "consumables", "bulk", "9.90", 0),
    ("Microsoft", "Windows 11 Pro", "operating-systems", "license", "259.00", 0),
    ("Fernwerk", "Ledgerline ERP", "office-software", "license", "780.00", 0),
    ("Adobe", "Creative Cloud All Apps", "design-software", "license", "1020.00", 0),
]

EXTRA_DEVICE_COUNTS = {
    "ThinkPad X1 Carbon Gen 12": 5,
    "Latitude 5450": 14,
    "iPad 10.9 (10th gen)": 6,
    "Galaxy Tab S9 FE": 4,
    "P2425H": 22,
    "LG 27UP850": 4,
    "ThinkPad Universal USB-C Dock": 12,
    "MX Master 3S": 14,
    "HL-L2350DW": 3,
}


def seed_extra(base: dict, stdout) -> None:
    """Many more people, devices in all states with history, requests in every step,
    purchase orders, consumable movements, licenses and problem reports."""
    rng = random.Random(42)
    today = timezone.localdate()
    now = timezone.now()
    admin, it = base["admin"], base["it"]
    categories, models = base["categories"], base["models"]
    storage, warehouse, hq = base["storage"], base["warehouse"], base["hq"]
    supplier = base["supplier"]

    # --- Organisation ----------------------------------------------------------
    departments = {}
    for name, code, cost_center, sort_order in EXTRA_DEPARTMENTS:
        department, _ = Department.objects.get_or_create(name=name, defaults={"code": code})
        department.code, department.cost_center, department.sort_order = code, cost_center, sort_order
        department.save()
        departments[name] = department

    people = []
    for index, (username, first, last, department_name, job) in enumerate(EXTRA_PEOPLE, start=1):
        user = base["make_user"](
            username, first, last, departments[department_name], staff=department_name == "IT"
        )
        user.job_title = job
        user.employee_number = f"{1000 + index}"
        user.phone = f"+49 89 1234-{100 + index}"
        user.save()
        people.append(user)
    by_name = {user.username: user for user in people}
    # Someone who left: kept for the history, but no longer active.
    leaver = base["make_user"]("kalt", "Klaus", "Alt", departments["Sales"])
    leaver.is_active = False
    leaver.save()
    # Someone who does not want reminder mails.
    by_name["mschmidt"].notification_settings = {"return_reminder": False}
    by_name["mschmidt"].save()
    # Support handles the daily work and only looks up the catalog; the rest is hidden.
    support_role = Role.objects.create(
        name="IT support",
        description="Requests, devices and problem reports; master data read-only.",
        permissions={
            **dict.fromkeys(("requests", "assets", "consumables", "licenses", "issues"), WRITE),
            **dict.fromkeys(("models", "categories", "manufacturers", "locations", "procurement"), READ),
        },
    )
    support_role.members.add(by_name["jkoch"])

    munich = Location.objects.create(name="Branch Munich", code="MUC", kind=Location.Kind.SITE)
    munich_storage = Location.objects.create(
        name="IT cabinet", code="MUC-IT", kind=Location.Kind.STORAGE, parent=munich
    )
    munich_desk = Location.objects.create(
        name="Reception", code="MUC-00", kind=Location.Kind.ROOM, parent=munich, is_pickup_point=True
    )
    Location.objects.create(name="Meeting room Atlas", code="HQ-2-11", kind=Location.Kind.ROOM, parent=hq)
    goods_in = Location.objects.create(
        name="Goods receipt", code="WH-GR", kind=Location.Kind.ROOM, parent=warehouse
    )

    brueckner = Supplier.objects.create(
        name="Brückner Systemhaus GmbH", customer_number="C-88213", email="orders@brueckner.example"
    )
    Supplier.objects.create(name="Amazon Business", website="https://www.amazon.de/business")

    # --- Catalog ---------------------------------------------------------------
    start = Category.objects.count() * 10
    for index, (code, name, icon, prefix, parent, singular, kind) in enumerate(EXTRA_CATEGORIES):
        sequence = None
        if prefix:
            sequence = NumberSequence.objects.create(
                code=f"category-{code}", name=name, prefix=prefix, pattern="{prefix}-{seq}", padding=4
            )
        categories[code] = Category.objects.create(
            code=code,
            name=name,
            icon=icon,
            kind=kind,
            item_name=singular,
            number_sequence=sequence,
            parent=categories.get(parent),
            allow_any_model=kind == "hardware" and code != "laptop-accessories",
            sort_order=start + index * 10,
        )
    for maker, name, category, tracking, price, warranty in EXTRA_MODELS:
        manufacturer, _ = Manufacturer.objects.get_or_create(name=maker)
        models[name] = AssetModel.objects.create(
            manufacturer=manufacturer,
            name=name,
            designation=name,
            category=categories[category],
            tracking=tracking,
            list_price=price,
            warranty_months=warranty or 24,
            default_supplier=brueckner if maker in ("Dell", "Brother", "LG") else supplier,
        )
    models["HL-L2350DW"].compatible_with.add(models["TN-2420 toner"])

    # --- Teams -------------------------------------------------------------------
    # Support gets everything not routed elsewhere; software requests go to the
    # license team, Ledgerline has its own. Requests from the basic data above stay
    # unassigned, so every tab of the lists has something to show.
    jkoch = by_name["jkoch"]
    support = Team.objects.create(name="IT-Support", code="SUP", is_default=True, sort_order=10)
    support.members.add(it, jkoch)
    software = Team.objects.create(name="Software & Lizenzen", code="SW", sort_order=20)
    software.members.add(admin, it)
    ledgerline = Team.objects.create(name="Ledgerline", code="NAV", sort_order=30)
    ledgerline.members.add(jkoch)
    for code in ("office-software", "design-software", "operating-systems"):
        categories[code].team = software
        categories[code].save()
    models["Ledgerline ERP"].team = ledgerline
    models["Ledgerline ERP"].save()
    for laptop_model in ("ThinkPad X1 Carbon Gen 12", "Latitude 5450", "ThinkPad T14 Gen 5"):
        models[laptop_model].compatible_with.add(
            models["ThinkPad Universal USB-C Dock"], models["USB-C cable 2 m"]
        )

    # --- Devices ---------------------------------------------------------------
    devices: dict[str, list[Asset]] = {}
    for model_index, (name, count) in enumerate(EXTRA_DEVICE_COUNTS.items(), start=50):
        model = models[name.removeprefix("LG ")]
        devices[name] = []
        for i in range(count):
            age = rng.randint(30, 1000)
            location = munich_storage if i % 5 == 4 else storage
            devices[name].append(
                asset_service.create_asset(
                    {
                        "model": model.pk,
                        "serial_number": f"{model.manufacturer.name[:2].upper()}{model_index:03d}{i:04d}",
                        "location": location.pk,
                        "supplier": model.default_supplier_id,
                        "purchase_date": today - timedelta(days=age),
                        "purchase_price": model.list_price,
                        "warranty_until": today
                        - timedelta(days=age)
                        + timedelta(days=30 * model.warranty_months),
                        "condition": rng.choice(
                            [
                                Asset.Condition.NEW,
                                Asset.Condition.GOOD,
                                Asset.Condition.GOOD,
                                Asset.Condition.WORN,
                            ]
                        ),
                        "hostname": f"NB-{model_index}{i:02d}" if model.category.code == "laptops" else "",
                    },
                    admin,
                )
            )

    # Work equipment: most people have a laptop, a monitor and a mouse.
    laptops = devices["Latitude 5450"][:8] + devices["ThinkPad X1 Carbon Gen 12"][:3]
    for user, laptop in zip(people, laptops, strict=False):
        asset_service.update_asset(laptop, {"assigned_to": user.pk}, it)
    for user, monitor in zip(people, devices["P2425H"][:14], strict=False):
        asset_service.update_asset(monitor, {"assigned_to": user.pk}, it)
    for user, mouse in zip(people[::2], devices["MX Master 3S"][:8], strict=False):
        asset_service.update_asset(mouse, {"assigned_to": user.pk}, it)
    for user, dock in zip(people[:5], devices["ThinkPad Universal USB-C Dock"][:5], strict=False):
        asset_service.update_asset(dock, {"assigned_to": user.pk}, it)
    asset_service.update_asset(devices["HL-L2350DW"][0], {"assigned_to": by_name["bschmitt"].pk}, it)
    asset_service.update_asset(devices["iPad 10.9 (10th gen)"][0], {"assigned_to": by_name["lweber"].pk}, it)

    # Devices in other states.
    in_repair = devices["Latitude 5450"][8]
    asset_service.update_asset(in_repair, {"status": Asset.Status.IN_REPAIR}, it)
    asset_service.record_event(
        in_repair,
        {
            "kind": AssetEvent.Kind.REPAIR,
            "description": "Sent to Dell for a keyboard replacement.",
            "cost": "89.00",
        },
        it,
    )
    asset_service.update_asset(
        devices["iPad 10.9 (10th gen)"][5],
        {"status": Asset.Status.LOST, "notes": "Lost on a business trip, reported to the police."},
        it,
    )
    asset_service.update_asset(
        devices["P2425H"][21], {"status": Asset.Status.RETIRED, "condition": Asset.Condition.DEFECTIVE}, it
    )
    asset_service.update_asset(
        devices["ThinkPad Universal USB-C Dock"][11],
        {"condition": Asset.Condition.DEFECTIVE, "is_loanable": False},
        it,
    )

    # Service history spread over the last year.
    history = [
        (AssetEvent.Kind.BATTERY_REPLACED, "Battery replaced after swelling.", "Battery 57 Wh", "120.00"),
        (AssetEvent.Kind.INSPECTION, "Annual electrical safety inspection (DGUV V3) passed.", "", None),
        (AssetEvent.Kind.MAINTENANCE, "Firmware and BIOS updated.", "", None),
        (AssetEvent.Kind.COMPONENT_REPLACED, "Display replaced after a crack.", "Display panel", "245.00"),
        (AssetEvent.Kind.NOTE, "User reports occasional Wi-Fi drops; drivers updated.", "", None),
    ]
    for asset in rng.sample(laptops + devices["P2425H"][:14], 12):
        kind, description, component, cost = rng.choice(history)
        asset_service.record_event(
            asset,
            {
                "kind": kind,
                "description": description,
                "component": component,
                "cost": cost,
                "occurred_at": now - timedelta(days=rng.randint(5, 330)),
            },
            it,
        )
    devices["ThinkPad Universal USB-C Dock"][0].consumables.add(models["USB-C cable 2 m"])

    # --- Consumables -----------------------------------------------------------
    stock = {}
    for name, location, quantity, minimum in [
        ("USB-C cable 2 m", storage, 30, 10),
        ("TN-2420 toner", storage, 2, 3),
        ("305 black ink cartridge", munich_storage, 5, 2),
        ("SX5x Battery 4680 mAh", munich_storage, 2, 2),
    ]:
        consumable, _ = Consumable.objects.get_or_create(
            model=models[name], location=location, defaults={"min_quantity": minimum}
        )
        move_consumable(consumable, quantity, ConsumableMovement.Reason.RECEIPT, admin, note="Initial stock")
        stock[name] = consumable
    for user in rng.sample(people, 6):
        move_consumable(stock["USB-C cable 2 m"], -1, ConsumableMovement.Reason.ISSUE, it, recipient=user)
    move_consumable(
        stock["TN-2420 toner"], -1, ConsumableMovement.Reason.ISSUE, it, recipient=by_name["bschmitt"]
    )
    move_consumable(
        stock["USB-C cable 2 m"],
        -2,
        ConsumableMovement.Reason.ADJUSTMENT,
        admin,
        note="Stocktaking difference",
    )

    # --- Licenses --------------------------------------------------------------
    windows = License.objects.create(
        model=models["Windows 11 Pro"],
        reference="Volume license 2025",
        seats=40,
        assign_to=License.AssignTo.DEVICE,
        supplier=brueckner,
        purchase_date=today - timedelta(days=300),
        purchase_price="7200.00",
    )
    for laptop in devices["Latitude 5450"][:12] + devices["ThinkPad X1 Carbon Gen 12"]:
        license_service.assign_license(windows, it, asset_id=laptop.pk)
    creative = License.objects.create(
        model=models["Creative Cloud All Apps"],
        reference="Team plan",
        seats=3,
        valid_from=today - timedelta(days=375),
        valid_until=today + timedelta(days=45),
        supplier=supplier,
    )
    for username in ("lneumann", "mbraun"):
        license_service.assign_license(creative, it, user_id=by_name[username].pk)
    expired = License.objects.create(
        model=models["Acrobat Pro"],
        reference="Old single licenses",
        seats=2,
        valid_from=today - timedelta(days=730),
        valid_until=today + timedelta(days=1),
    )
    license_service.assign_license(expired, it, user_id=by_name["bschmitt"].pk)
    License.objects.filter(pk=expired.pk).update(valid_until=today - timedelta(days=12))
    nav = License.objects.create(
        model=models["Ledgerline ERP"],
        reference="ERP user licenses",
        seats=10,
        supplier=brueckner,
        purchase_date=today - timedelta(days=500),
        purchase_price="7800.00",
    )
    for username in ("cmeyer", "hkrause", "nlange"):
        license_service.assign_license(nav, it, user_id=by_name[username].pk)
    m365 = License.objects.get(model__name="365 Business Standard")
    for user in people[:18]:
        license_service.assign_license(m365, it, user_id=user.pk)

    # --- Requests in every step ------------------------------------------------
    def submit(user, title, items, duration="temporary", start=0, days=3, notes=""):
        data = {
            "title": title,
            "duration": duration,
            "start_date": today + timedelta(days=start),
            "notes": notes,
        }
        if duration == "temporary":
            data["end_date"] = today + timedelta(days=start + days - 1)
        return workflow.submit(user, data, items, created_by=user, allow_past_start=start < 0)

    def confirm(asset_request, comment=""):
        return workflow.confirm(asset_request, it, {}, comment)

    def mark_ready(asset_request, pickup_days=1, location=None):
        pickup = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=pickup_days)
        workflow.auto_allocate(asset_request, it)
        return workflow.mark_ready(
            asset_request, it, pickup_at=pickup, pickup_location_id=location.pk if location else None
        )

    def hand_out(asset_request):
        confirm(asset_request)
        mark_ready(asset_request, pickup_days=0)
        return workflow.hand_out(asset_request, it, method=Handover.Method.DIRECT)

    tablets, monitors = categories["tablets"], categories["monitors"]
    submit(
        by_name["mschmidt"],
        "Trade fair Hanover",
        [{"category": tablets.pk, "quantity": 3}, {"asset_model": models["MX Master 3S"].pk, "quantity": 3}],
        start=10,
        days=5,
        notes="Booth demo, tablets with kiosk mode please.",
    )
    submit(
        by_name["sschulz"],
        "Ergonomic workplace",
        [{"description": "Split keyboard (ergonomic)", "quantity": 1, "category": categories["input"].pk}],
        duration="permanent",
    )
    submit(
        by_name["mbraun"],
        "Photo editing",
        [{"asset_model": models["Acrobat Pro"].pk, "quantity": 1}],
        duration="permanent",
    )
    confirm(
        submit(
            by_name["jwagner"],
            "Customer workshop",
            [{"category": categories["laptops"].pk, "quantity": 2}],
            start=6,
            days=2,
        ),
        comment="Two Latitudes are reserved for you.",
    )
    new_colleague = submit(
        by_name["fzimmermann"],
        "New colleague in Munich",
        [
            {"category": monitors.pk, "quantity": 2},
            {"asset_model": models["ThinkPad Universal USB-C Dock"].pk, "quantity": 1},
        ],
        duration="permanent",
    )
    new_colleague.assignee = jkoch
    new_colleague.save(update_fields=["assignee"])
    confirm(new_colleague)
    mark_ready(new_colleague, location=munich_desk)

    # Routed to the Ledgerline team by the model, waiting for someone to pick it up.
    submit(
        by_name["lweber"],
        "Ledgerline access for the monthly reports",
        [{"asset_model": models["Ledgerline ERP"].pk, "quantity": 1}],
        duration="permanent",
    )

    hand_out(
        submit(
            by_name["tfischer"],
            "Business trip Vienna",
            [{"category": tablets.pk, "quantity": 1}],
            start=-3,
            days=7,
        )
    )
    hand_out(
        submit(
            by_name["pwolf"],
            "Inventory scanners",
            [{"asset_model": models["Galaxy Tab S9 FE"].pk, "quantity": 2}],
            start=-14,
            days=12,
        )
    )
    webinar = hand_out(
        submit(
            by_name["lneumann"],
            "Webinar series",
            [{"asset_model": models["Evolve2 40 SE"].pk, "quantity": 2}],
            start=-30,
            days=5,
        )
    )
    workflow.return_devices(webinar, it)
    hand_out(
        submit(
            by_name["abecker"],
            "Replacement laptop",
            [{"asset_model": models["ThinkPad X1 Carbon Gen 12"].pk, "quantity": 1}],
            duration="permanent",
        )
    )
    workflow.reject(
        submit(
            by_name["jwerner"],
            "Second monitor at home",
            [{"asset_model": models["27UP850"].pk, "quantity": 1}],
            duration="permanent",
        ),
        it,
        "Home office equipment is handled by HR; please request it there.",
    )
    workflow.cancel(
        submit(
            by_name["dhoffmann"],
            "Headset",
            [{"category": categories["headsets"].pk, "quantity": 1}],
            duration="permanent",
        ),
        by_name["dhoffmann"],
    )

    # Smartphones need the department's approval; the team lead approves for customer service.
    categories["phones"].requires_approval = True
    categories["phones"].save(update_fields=["requires_approval"])
    departments["Customer Service"].approvers.add(by_name["jwagner"])
    submit(
        by_name["sschulz"],
        "On-call phone",
        [{"category": categories["phones"].pk, "quantity": 1}],
        duration="permanent",
        notes="For the weekend on-call duty.",
    )
    workflow.approve(
        submit(
            by_name["dhoffmann"],
            "Smartphone for customer visits",
            [{"asset_model": models["Galaxy A56"].pk, "quantity": 1}],
            duration="permanent",
        ),
        by_name["jwagner"],
        "Agreed, David visits customers from next month on.",
    )

    # --- Procurement -----------------------------------------------------------
    def order(supplier_, lines, notes=""):
        return order_service.create_order(
            {"supplier": supplier_.pk, "delivery_location": goods_in.pk, "notes": notes},
            [{"asset_model": models[name].pk, "quantity": quantity} for name, quantity in lines],
            admin,
        )

    order(brueckner, [("Latitude 5450", 5)], notes="Replacement of the 2021 notebooks.")
    in_transit = order(brueckner, [("P2425H", 10), ("USB-C cable 2 m", 20)])
    order_service.mark_ordered(in_transit, today - timedelta(days=3), today + timedelta(days=4), "AB-552190")
    partial = order(supplier, [("ThinkPad Universal USB-C Dock", 6)])
    order_service.mark_ordered(partial, today - timedelta(days=12), today - timedelta(days=2), "BE-77120")
    line = partial.lines.first()
    order_service.receive(
        partial,
        [{"line": line.pk, "quantity": 3, "serial_numbers": ["LE0990001", "LE0990002", "LE0990003"]}],
        it,
    )
    done = order(brueckner, [("TN-2420 toner", 5)])
    order_service.mark_ordered(done, today - timedelta(days=40), today - timedelta(days=35), "AB-540033")
    order_service.receive(done, [{"line": done.lines.first().pk, "quantity": 5, "location": storage.pk}], it)
    order_service.cancel(order(supplier, [("iPad 10.9 (10th gen)", 4)], notes="Project postponed."))

    # --- Problem reports -------------------------------------------------------
    def report(user, kind, description):
        asset = Asset.objects.filter(assigned_to=user).first()
        assert asset is not None  # everyone reporting here got devices above
        return issue_service.report_issue(asset, user, kind, description)

    report(by_name["dhoffmann"], AssetIssue.Kind.DEFECT, "Battery is empty after two hours.")
    flicker = report(
        by_name["jwagner"], AssetIssue.Kind.DAMAGE, "Monitor flickers when the cable is touched."
    )
    flicker.assignee = it
    flicker.save(update_fields=["assignee"])
    issue_service.update_issue(flicker, it, AssetIssue.Status.IN_PROGRESS, by_it=True)
    issue_service.post_message(
        flicker, it, "Does it also flicker with the spare cable from the IT desk?", by_it=True
    )
    issue_service.post_message(
        flicker, by_name["jwagner"], "Yes, with that cable too, but less often.", by_it=False
    )
    issue_service.update_issue(
        report(by_name["lkrueger"], AssetIssue.Kind.OTHER, "Laptop is very slow since the last update."),
        it,
        AssetIssue.Status.RESOLVED,
        "Disk was full; temporary files removed and storage doubled.",
        by_it=True,
    )

    stdout.write(
        f"Extended demo data: {User.objects.count()} users, {Asset.objects.count()} devices, "
        f"{Department.objects.count()} departments."
    )
