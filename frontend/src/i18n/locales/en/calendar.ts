export default {
  title: 'Calendar',
  subtitle: 'Reservations, pickups, returns, deliveries and warranty ends at a glance.',
  previous: 'Previous',
  next: 'Next',
  views: { month: 'Month', week: 'Week', list: 'List' },
  kinds: {
    loan: 'Reservation',
    pickup: 'Pickup',
    return: 'Return due',
    delivery: 'Delivery',
    warranty: 'Warranty ends',
  },
  titles: {
    pickup: 'Pickup: {name}',
    return: 'Return: {name}',
    delivery: 'Delivery: {supplier}',
    warranty: 'Warranty ends: {count} device | Warranty ends: {count} devices',
  },
  legend: { confirmed: 'confirmed', tentative: 'not yet confirmed', overdue: 'overdue' },
  overdueSince: 'Overdue since {date}',
  permanentHidden: 'Permanent hand-outs are not shown.',
}
