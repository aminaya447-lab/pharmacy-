import datetime

import operations as ops

# ---------------------------------------------- previous (Products / Suppliers)
print("Products:")
for p in ops.list_products():
    print("  ", p)

print("Product 1:", ops.get_product(1))
print("Search 'Pana':", ops.list_products("Pana"))
print("Summary:", ops.report_summary())
print("Per supplier:", ops.report_products_per_supplier())
print("HAVING:", ops.report_suppliers_with_many_products())
print("Above average:", ops.report_above_average_price())

# ------------------------------------------------------------- new schema
print("\n--- NEW SCHEMA ---")
print("Branches:", ops.list_branches())
print("Medicines:", ops.list_medicines())
print("Search 'Pana':", ops.list_medicines("Pana"))
print("Customers:", ops.list_customers())
print("Employees:", ops.list_employees())
print("Suppliers (LEFT JOIN):", ops.list_all_suppliers())
print("Inventory:", ops.list_inventory())
print("Purchases:", ops.list_purchases())
print("Purchase 1 lines:", ops.purchase_lines(1))
print("Sales:", ops.list_sales())
print("Sale 1 lines:", ops.sale_lines(1))
print("Sale 1 prescription:", ops.sale_prescription(1))
print("Prescriptions:", ops.list_prescriptions())

print("\n--- NEW REPORTS ---")
print("Summary:", ops.rep_medicine_summary())
print("Sales detail:", ops.rep_sales_detail())
print("Sold per medicine:", ops.rep_sold_per_medicine())
print("Sold more than once:", ops.rep_sold_more_than_once())
print("Per employee:", ops.rep_sales_per_employee())
print("Per payment:", ops.rep_sales_per_payment())
print("Branch staff:", ops.rep_branch_staff())
print("Branch stock:", ops.rep_branch_stock())
print("Expiring:", ops.rep_expiring(datetime.date(2027, 12, 31)))
print("Above average:", ops.rep_medicines_above_average())
print("Never purchased:", ops.rep_medicines_never_purchased())
print("Customers without sales:", ops.rep_customers_without_sales())