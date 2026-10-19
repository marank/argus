export default {
  title: 'Kalender',
  subtitle:
    'Reservierungen, Abholungen, Rückgaben, Lieferungen, Garantie- und Lizenzenden auf einen Blick.',
  previous: 'Zurück',
  next: 'Weiter',
  views: { month: 'Monat', week: 'Woche', list: 'Liste' },
  kinds: {
    loan: 'Reservierung',
    pickup: 'Abholung',
    return: 'Rückgabe fällig',
    delivery: 'Lieferung',
    warranty: 'Garantie endet',
    license: 'Lizenz endet',
  },
  titles: {
    pickup: 'Abholung: {name}',
    return: 'Rückgabe: {name}',
    delivery: 'Lieferung: {supplier}',
    warranty: 'Garantie endet: {count} Gerät | Garantie endet: {count} Geräte',
    license: 'Lizenz endet: {name}',
  },
  legend: { confirmed: 'bestätigt', tentative: 'noch nicht bestätigt', overdue: 'überfällig' },
  overdueSince: 'Überfällig seit {date}',
  permanentHidden: 'Dauerhafte Ausgaben werden nicht angezeigt.',
}
