'''
Copy subscriptions from one stripe account to another
'''
import stripe
import datetime
from pymongo import MongoClient
from pprint import pprint

source = "YOUR_SOURCE_ACCOUNT_STRIPE_KEY"
dest = "YOUR_DESTINATION_ACCOUNT_STRIPE_KEY"

# if you need to update your database, you'll need to 
# add a database string here. In my case, I'm using MongoDB
mongodb_uri = 'MONGDB_URL'
db = MongoClient(mongodb_uri)['database-name']

old_customers = stripe.Customer.list(limit=100, starting_after='cus_id', api_key=source)

def time_str(timestamp):
  return datetime.datetime.fromtimestamp(
      int(timestamp)
  ).strftime('%Y-%m-%d %H:%M:%S')

for customer in old_customers.data:
  print('------------------------')
  print()

  if not customer.subscriptions.data:
    # if no subscription, just skip this customer
    print('No subscriptions found for:', customer.email, customer.id, '- skipping.')
    continue

  subscription = customer.subscriptions.data[0]
  plan = subscription.plan.id
  plan_end_date = subscription.current_period_end
  
  if subscription.cancel_at_period_end:
    print('skip customer:', customer.email, 'already cancelled.')
    continue
  
  print()
  print('Customer on source account is:', customer.email, customer.id)
  print('Plan on source account:', plan)
  print('Plan on source account ends on:', time_str(plan_end_date))
  print('Original subscription id:', subscription.id)
  print()
  
  dest_customer = stripe.Customer.retrieve(customer.id, api_key=dest)
  
  # if the customer already has a subscription
  # don't need to do anything
  if dest_customer.subscriptions.total_count >= 1:
    print('New subscription already created for', dest_customer.email, ', skipping. Although you might want to check the database.')
    continue

  # your unique plan names here
  new_plan = ''
  if plan == 'standard-monthly':
    new_plan = 'pro-monthly'
  elif plan == 'standard-annual':
    new_plan = 'pro-annual'
  elif plan == 'basic-monthly':
    new_plan = 'legacy-monthly'
  elif plan == 'basic-annual':
    new_plan = 'legacy-annual'

  if not new_plan:
    print('No corresponding plan found for:', plan)
    continue
  
  if not plan_end_date:
    print('Plan end date not found for:', customer.id)
    continue
  
  print()
  print('Now copying to dest customer:', dest_customer.email, dest_customer.id)
  print('New plan is:', new_plan)
  print('New plan trial period ends:', time_str(plan_end_date))
  print()

  # create the subscription for the new customer
  dest_subscription = stripe.Subscription.create(
    customer=dest_customer.id,
    items=[{ "plan": new_plan }],
    prorate=False,
    trial_end=plan_end_date,
    api_key=dest
  )

  print()
  print('New subscription created:', dest_subscription.id)
  print('New subscription type:', dest_subscription.plan.nickname)
  print('New subscription start:', time_str(dest_subscription.start))
  print()

  # need to update the subscription id in our database
  db_customer = db.users.find_one({'email': dest_customer.email})
  if not db_customer:
    print('Something went wrong. Customer', dest_customer.email, 'not found in db')
    
  if not dest_customer.email:
    print('Customer does not have email, will try to update by stripeId')
    db.users.update(
      {"stripeId": dest_customer.id}, \
      {"$set": { \
        "stripeId": dest_customer.id, \
        "subscriptionId": dest_subscription.id, \
        "hasSubscription": True \
      }},
      multi=True)
  else:
    db.users.update(
      {"email": dest_customer.email}, \
      {"$set": { \
        "stripeId": dest_customer.id, \
        "subscriptionId": dest_subscription.id, \
        "hasSubscription": True \
      }},
      multi=True)

  print(dest_customer.email, 'updated in database')

  # finally, cancel the subscription on the source stripe account
  old_sub = stripe.Subscription.retrieve(subscription.id, api_key=source)
  old_sub.delete(at_period_end=True)

  print('Old subscription,', subscription.id, 'was cancelled. Next!')
  print()
  print()