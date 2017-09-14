import conekta

conekta.api_key = 'key_ReaoWd2MyxP5QdUWKSuXBQ'
conekta.api_version = "2.0.0"
conekta.locale = 'es'

def create_payment_method(customer, token_id):
    source = customer.createPaymentSource({
        "type": "card",
        "token_id": token_id
    })
    if source:
        return True
    else:
        return False
    
def create_subscription(customer, token_id):
    if not customer.payment_sources[0]:
        source = create_payment_method(customer, token_id)
        subscription = customer.createSubscription({ "plan": "plan-mensual-pro" })
    else:
        subscription = customer.createSubscription({ "plan": "plan-mensual-pro" })
    if subscription.status == 'active':
        return True
    else:
        return False
    
def resume_subscription(customer):
    subscription = customer.subscription.update({ "plan": "plan-mensual-pro" })
    if subscription.status == 'active':
        return True
    else:
        return False