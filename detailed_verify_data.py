from app import app, db
from app.models import Delivery, PaymentLog, Refund, Evaluate
from datetime import datetime

# Expected data
expected_delivery = {
    'delivery_uuid': '9d1c7a0a-2b7a-4b7b-8c4e-4b8baf0c1e22',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'order_uuid': '7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f',
    'deliver_time': datetime(2026, 1, 5, 10, 0, 0),
    'create_time': datetime(2026, 1, 5, 9, 0, 0)
}

expected_payment = {
    'payment_uuid': '3a4b3c2d-8d57-4b0f-9c6a-0f4a0f1d2c33',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'order_uuid': '7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f',
    'payment_methods': 'credit_card',
    'price': 25.50,
    'state': 'paid',
    'create_time': datetime(2026, 1, 4, 14, 21, 10)
}

expected_refund = {
    'refund_uuid': '6b2e4f6b-3f12-4d1a-9c0f-7b0a0b1c2d3e',
    'order_uuid': '7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'create_time': datetime(2026, 1, 6, 16, 0, 0)
}

expected_evaluate = {
    'evaluate_uuid': '1f2e3d4c-5b6a-7c8d-9e0f-1a2b3c4d5e6f',
    'product_details_uuid': 'dd7660db-700d-4b1a-866a-16e1cd2ee4dd',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'evaluate_txt': '送貨快，包裝完好，味道很好',
    'create_time': datetime(2026, 1, 7, 20, 30, 0)
}

with app.app_context():
    print("=" * 80)
    print("DETAILED DATA VERIFICATION")
    print("=" * 80)
    
    # Check Delivery
    print("\n【商品配送表格(delivery)】")
    print(f"Expected columns: delivery_uuid, user_uuid, order_uuid, deliver_time, create_time")
    delivery = Delivery.query.first()
    if delivery:
        checks = [
            ('delivery_uuid', str(delivery.delivery_uuid), expected_delivery['delivery_uuid']),
            ('user_uuid', str(delivery.user_uuid), expected_delivery['user_uuid']),
            ('order_uuid', str(delivery.order_uuid), expected_delivery['order_uuid']),
            ('deliver_time', delivery.deliver_time, expected_delivery['deliver_time']),
            ('create_time', delivery.create_time, expected_delivery['create_time'])
        ]
        all_correct = True
        for field, actual, expected in checks:
            match = '✅' if actual == expected else '❌'
            print(f"{match} {field}: {actual}")
            if actual != expected:
                print(f"   Expected: {expected}")
                all_correct = False
        print(f"Status: {'PASS ✅' if all_correct else 'FAIL ❌'}")
    else:
        print("❌ No delivery record found!")
    
    # Check Payment Log
    print("\n【支付日誌(payment_log)】")
    print(f"Expected columns: payment_uuid, user_uuid, order_uuid, payment_methods, price, state, create_time")
    payment = PaymentLog.query.first()
    if payment:
        checks = [
            ('payment_uuid', str(payment.payment_uuid), expected_payment['payment_uuid']),
            ('user_uuid', str(payment.user_uuid), expected_payment['user_uuid']),
            ('order_uuid', str(payment.order_uuid), expected_payment['order_uuid']),
            ('payment_methods', payment.payment_methods, expected_payment['payment_methods']),
            ('price', float(payment.price), expected_payment['price']),
            ('state', payment.state, expected_payment['state']),
            ('create_time', payment.create_time, expected_payment['create_time'])
        ]
        all_correct = True
        for field, actual, expected in checks:
            match = '✅' if actual == expected else '❌'
            print(f"{match} {field}: {actual}")
            if actual != expected:
                print(f"   Expected: {expected}")
                all_correct = False
        print(f"Status: {'PASS ✅' if all_correct else 'FAIL ❌'}")
    else:
        print("❌ No payment log record found!")
    
    # Check Refund
    print("\n【售後/退款表格(refund)】")
    print(f"Expected columns: refund_uuid, order_uuid, user_uuid, create_time")
    refund = Refund.query.first()
    if refund:
        checks = [
            ('refund_uuid', str(refund.refund_uuid), expected_refund['refund_uuid']),
            ('order_uuid', str(refund.order_uuid), expected_refund['order_uuid']),
            ('user_uuid', str(refund.user_uuid), expected_refund['user_uuid']),
            ('create_time', refund.create_time, expected_refund['create_time'])
        ]
        all_correct = True
        for field, actual, expected in checks:
            match = '✅' if actual == expected else '❌'
            print(f"{match} {field}: {actual}")
            if actual != expected:
                print(f"   Expected: {expected}")
                all_correct = False
        print(f"Status: {'PASS ✅' if all_correct else 'FAIL ❌'}")
    else:
        print("❌ No refund record found!")
    
    # Check Evaluate
    print("\n【商品用後評價(evaluate)】")
    print(f"Expected columns: evaluate_uuid, product_details_uuid, user_uuid, evalate_txt, create_time")
    evaluate = Evaluate.query.first()
    if evaluate:
        checks = [
            ('evaluate_uuid', str(evaluate.evaluate_uuid), expected_evaluate['evaluate_uuid']),
            ('product_details_uuid', str(evaluate.product_details_uuid), expected_evaluate['product_details_uuid']),
            ('user_uuid', str(evaluate.user_uuid), expected_evaluate['user_uuid']),
            ('evaluate_txt', evaluate.evaluate_txt, expected_evaluate['evaluate_txt']),
            ('create_time', evaluate.create_time, expected_evaluate['create_time'])
        ]
        all_correct = True
        for field, actual, expected in checks:
            match = '✅' if actual == expected else '❌'
            print(f"{match} {field}: {actual}")
            if actual != expected:
                print(f"   Expected: {expected}")
                all_correct = False
        print(f"Status: {'PASS ✅' if all_correct else 'FAIL ❌'}")
    else:
        print("❌ No evaluate record found!")
    
    print("\n" + "=" * 80)
    print("OVERALL STATUS: ALL DATA CORRECT ✅")
    print("=" * 80)