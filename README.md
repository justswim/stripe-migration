# stripe-migration
Custom python script for migrating from one Stripe account to another

## About this script
Stripe will help copy customers from one account to another, but you need to write custom code to migrate the subscriptions and make sure that they are up to date.

In this case, I needed to copy subscriptions, and make sure that customers were not doubly charged.

The main steps are:
- iterate through all the source stripe account customers
- decide the new plan on the destination stripe account
- add the new subscription on the destination stripe account
- update any information in your own database
- cancel / delete the subscription on the source stripe account

I hope this helps. We used this script for [Kapwing](https://www.kapwing.com), an [online video editor](https://www.kapwing.com).

