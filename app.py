import datetime

import pandas as pd
import pyodbc
import streamlit as st

import operations as ops

st.set_page_config(page_title="Pharmacy Database App", page_icon="💊", layout="wide")
st.title("💊 Pharmacy Database App")

PAYMENT_METHODS = ["Cash", "Card", "Insurance", "Online"]


# ================================================================= helpers
def show_table(rows, columns):
    if rows:
        st.dataframe(pd.DataFrame(rows, columns=columns), hide_index=True)
    else:
        st.info("No data found.")


def clean_text(text):
    """Empty text box -> NULL."""
    text = text.strip()
    return text if text else None


def req(text, label):
    """Mandatory text box."""
    text = text.strip()
    if not text:
        raise ValueError(f"{label} cannot be empty.")
    return text


def pick(label, rows, key, current=None, allow_none=False, label_fn=None):
    """Dropdown built from query rows. Shows a label, returns the ID (first column)."""
    label_fn = label_fn or (lambda r: r[1])
    labels = {r[0]: label_fn(r) for r in rows}
    ids = list(labels)
    if allow_none:
        ids = [None] + ids
    index = ids.index(current) if current in ids else 0
    return st.selectbox(
        label,
        ids,
        index=index,
        key=key,
        format_func=lambda i: "— none —" if i is None else f"{i} - {labels[i]}",
    )


def run(action, success):
    """Run a database action; show a friendly message on failure.
    On success keep a message for after the rerun, so tables show fresh data."""
    try:
        result = action()
    except pyodbc.IntegrityError:
        st.error(
            "Rejected by a database rule: duplicate value, CHECK rule, or a "
            "FOREIGN KEY (e.g. the record is still used by other records)."
        )
        return
    except Exception as e:
        st.error(f"Error: {e}")
        return
    st.session_state["flash"] = success(result) if callable(success) else success
    st.rerun()


def delete_block(prefix, rows, label_fn, delete_fn, what, warning=None):
    if not rows:
        st.info("No records to delete.")
        return
    rid = pick(f"{what} to delete", rows, f"{prefix}_del_pick", label_fn=label_fn)
    if warning:
        st.warning(warning)
    confirm = st.checkbox("Yes, I want to delete it", key=f"{prefix}_del_ok_{rid}")
    if st.button(f"Delete {what}", key=f"{prefix}_del_btn"):
        if not confirm:
            st.warning("Please confirm deletion first.")
        else:
            run(lambda: delete_fn(rid), f"{what} deleted.")


def collect_lines(prefix, n, medicines):
    """Read n (medicine, quantity) widgets; merge a medicine picked twice."""
    lines = {}
    for i in range(int(n)):
        c1, c2 = st.columns([3, 1])
        with c1:
            mid = pick(f"Medicine {i + 1}", medicines, f"{prefix}_med_{i}")
        with c2:
            qty = st.number_input("Quantity", min_value=1, step=1, key=f"{prefix}_qty_{i}")
        lines[mid] = lines.get(mid, 0) + int(qty)
    return lines


# flash message from the previous action
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))


# ========================================== PREVIOUS PAGES (Products)
def supplier_picker(label, current=None, key=None):
    """Mandatory supplier dropdown (old Suppliers table). Returns SupplierID."""
    suppliers = ops.list_suppliers()
    names = {sid: name for sid, name in suppliers}
    ids = list(names)
    index = ids.index(current) if current in ids else 0
    return st.selectbox(
        label,
        ids,
        index=index,
        format_func=lambda i: f"{i} - {names[i]}",
        key=key,
    )


def page_products_view():
    st.header("View / Search Products")
    search_text = st.text_input("Search by product name or ID")
    rows = ops.list_products(search_text.strip())
    show_table(rows, ["Product ID", "Product Name", "Price", "Quantity", "Supplier"])


def page_products_add():
    st.header("Add New Product")

    if not ops.list_suppliers():
        st.warning("Add a supplier first.")
    else:
        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            quantity = st.number_input("Quantity", min_value=0, step=1)
            supplier_id = supplier_picker("Supplier")
            submitted = st.form_submit_button("Add Product")

        if submitted:
            try:
                if not name.strip():
                    raise ValueError("Product name cannot be empty.")
                ops.add_product(name.strip(), price, quantity, supplier_id)
                st.success("Product added successfully.")
            except pyodbc.IntegrityError:
                st.error("Rejected by a database rule (CHECK or FOREIGN KEY).")
            except Exception as e:
                st.error(f"Error adding product: {e}")


def page_products_update():
    st.header("Update Product")
    product_id = st.number_input("Enter Product ID", min_value=1, step=1)
    product = ops.get_product(product_id)

    if product is None:
        st.warning("No product found with that ID.")
    else:
        st.write("Current product details:")
        show_table(
            [product],
            ["Product ID", "Product Name", "Price", "Quantity", "Supplier ID", "Supplier"],
        )

        with st.form("update_product_form"):
            name = st.text_input("Product Name", value=product[1], key=f"n{product_id}")
            price = st.number_input(
                "Price", min_value=0.0, value=float(product[2]),
                format="%.2f", key=f"p{product_id}",
            )
            quantity = st.number_input(
                "Quantity", min_value=0, value=int(product[3]),
                step=1, key=f"q{product_id}",
            )
            supplier_id = supplier_picker("Supplier", product[4], key=f"s{product_id}")
            submitted = st.form_submit_button("Update Product")

        if submitted:
            try:
                if not name.strip():
                    raise ValueError("Product name cannot be empty.")
                n = ops.update_product(product_id, name.strip(), price, quantity, supplier_id)
                if n:
                    st.success("Product updated successfully.")
                else:
                    st.warning("No product was updated.")
            except pyodbc.IntegrityError:
                st.error("Rejected by a database rule (CHECK or FOREIGN KEY).")
            except Exception as e:
                st.error(f"Error updating product: {e}")


def page_products_delete():
    st.header("Delete Product")
    product_id = st.number_input("Enter Product ID", min_value=1, step=1)
    product = ops.get_product(product_id)

    if product is None:
        st.warning("No product found with that ID.")
    else:
        st.write("Product to delete:")
        show_table(
            [product],
            ["Product ID", "Product Name", "Price", "Quantity", "Supplier ID", "Supplier"],
        )
        confirm = st.checkbox("Yes, I want to delete this product")

        if st.button("Delete Product"):
            if not confirm:
                st.warning("Please confirm deletion first.")
            else:
                try:
                    n = ops.delete_product(product_id)
                    if n:
                        st.success("Product deleted successfully.")
                    else:
                        st.warning("No product was deleted.")
                except Exception as e:
                    st.error(f"Error deleting product: {e}")


def page_products_reports():
    st.header("Reports (Products)")

    n, max_p, min_p, avg_p = ops.report_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", n)
    c2.metric("Highest price", f"{(max_p or 0):.2f}")
    c3.metric("Lowest price", f"{(min_p or 0):.2f}")
    c4.metric("Average price", f"{(avg_p or 0):.2f}")

    tabs = st.tabs(["GROUP BY (COUNT)", "GROUP BY (SUM)", "HAVING", "Subquery"])
    with tabs[0]:
        st.caption("Number of products per supplier (book Q10)")
        show_table(ops.report_products_per_supplier(),
                   ["Supplier ID", "Supplier", "Number of Products"])
    with tabs[1]:
        st.caption("Stock value (price x quantity) per supplier (book Q4 + GROUP BY)")
        show_table(ops.report_stock_value_per_supplier(),
                   ["Supplier", "Stock Value"])
    with tabs[2]:
        st.caption("Suppliers with more than one product (book Q11)")
        show_table(ops.report_suppliers_with_many_products(),
                   ["Supplier ID", "Supplier", "Number of Products"])
    with tabs[3]:
        st.caption("Products priced above the average (subquery in WHERE)")
        show_table(ops.report_above_average_price(),
                   ["Product ID", "Product", "Price"])


# ================================================== NEW SCHEMA PAGES
# ------------------------------------------------------------------ Branch
def page_branches():
    st.header("Branches")
    t = st.tabs(["List", "Add", "Update", "Delete"])

    with t[0]:
        show_table(ops.list_branches(), ["Branch ID", "Name", "Location", "Phone"])

    with t[1]:
        with st.form("br_add"):
            name = st.text_input("Branch name", key="br_add_name")
            loc = st.text_input("Location", key="br_add_loc")
            phone = st.text_input("Phone", key="br_add_phone")
            ok = st.form_submit_button("Add branch")
        if ok:
            run(lambda: ops.add_branch(req(name, "Branch name"), req(loc, "Location"),
                                       clean_text(phone)), "Branch added.")

    with t[2]:
        rows = ops.list_branches()
        if not rows:
            st.info("No branches yet.")
        else:
            bid = pick("Branch", rows, "br_upd_pick")
            rec = ops.get_branch(bid)
            with st.form("br_upd"):
                name = st.text_input("Branch name", value=rec[1], key=f"br_upd_name_{bid}")
                loc = st.text_input("Location", value=rec[2], key=f"br_upd_loc_{bid}")
                phone = st.text_input("Phone", value=rec[3] or "", key=f"br_upd_phone_{bid}")
                ok = st.form_submit_button("Update branch")
            if ok:
                run(lambda: ops.update_branch(bid, req(name, "Branch name"), req(loc, "Location"),
                                              clean_text(phone)), "Branch updated.")

    with t[3]:
        delete_block("br", ops.list_branches(), lambda r: r[1], ops.delete_branch, "Branch",
                     "A branch with employees or inventory batches cannot be deleted.")


# ---------------------------------------------------------------- Medicine
def page_medicines():
    st.header("Medicines")
    t = st.tabs(["Search", "Add", "Update", "Delete"])

    with t[0]:
        text = st.text_input("Search by name, barcode or ID", key="med_search")
        show_table(ops.list_medicines(text.strip()), ["Medicine ID", "Name", "Barcode", "Price"])

    with t[1]:
        with st.form("med_add"):
            name = st.text_input("Medicine name", key="med_add_name")
            barcode = st.text_input("Barcode", key="med_add_barcode")
            price = st.number_input("Price", min_value=0.0, format="%.2f", key="med_add_price")
            ok = st.form_submit_button("Add medicine")
        if ok:
            run(lambda: ops.add_medicine(req(name, "Name"), req(barcode, "Barcode"), price),
                "Medicine added.")

    with t[2]:
        rows = ops.list_medicines()
        if not rows:
            st.info("No medicines yet.")
        else:
            mid = pick("Medicine", rows, "med_upd_pick")
            rec = ops.get_medicine(mid)
            with st.form("med_upd"):
                name = st.text_input("Medicine name", value=rec[1], key=f"med_upd_name_{mid}")
                barcode = st.text_input("Barcode", value=rec[2], key=f"med_upd_barcode_{mid}")
                price = st.number_input("Price", min_value=0.0, value=float(rec[3]),
                                        format="%.2f", key=f"med_upd_price_{mid}")
                ok = st.form_submit_button("Update medicine")
            if ok:
                run(lambda: ops.update_medicine(mid, req(name, "Name"), req(barcode, "Barcode"),
                                                price), "Medicine updated.")

    with t[3]:
        delete_block("med", ops.list_medicines(), lambda r: r[1], ops.delete_medicine, "Medicine",
                     "Deleting a medicine also deletes its sale lines, purchase lines and "
                     "inventory links (ON DELETE CASCADE). A medicine used by a supplier is blocked.")


# ---------------------------------------------------------------- Customer
def page_customers():
    st.header("Customers")
    t = st.tabs(["Search", "Add", "Update", "Delete"])

    with t[0]:
        text = st.text_input("Search by name, phone, email or ID", key="cus_search")
        show_table(ops.list_customers(text.strip()), ["Customer ID", "Name", "Phone", "Email"])

    with t[1]:
        with st.form("cus_add"):
            name = st.text_input("Name", key="cus_add_name")
            phone = st.text_input("Phone", key="cus_add_phone")
            email = st.text_input("Email", key="cus_add_email")
            ok = st.form_submit_button("Add customer")
        if ok:
            run(lambda: ops.add_customer(req(name, "Name"), clean_text(phone), clean_text(email)),
                "Customer added.")

    with t[2]:
        rows = ops.list_customers()
        if not rows:
            st.info("No customers yet.")
        else:
            cid = pick("Customer", rows, "cus_upd_pick")
            rec = ops.get_customer(cid)
            with st.form("cus_upd"):
                name = st.text_input("Name", value=rec[1], key=f"cus_upd_name_{cid}")
                phone = st.text_input("Phone", value=rec[2] or "", key=f"cus_upd_phone_{cid}")
                email = st.text_input("Email", value=rec[3] or "", key=f"cus_upd_email_{cid}")
                ok = st.form_submit_button("Update customer")
            if ok:
                run(lambda: ops.update_customer(cid, req(name, "Name"), clean_text(phone),
                                                clean_text(email)), "Customer updated.")

    with t[3]:
        delete_block("cus", ops.list_customers(), lambda r: r[1], ops.delete_customer, "Customer",
                     "A customer who has sales cannot be deleted.")


# ---------------------------------------------------------------- Employee
def page_employees():
    st.header("Employees")
    t = st.tabs(["List", "Add", "Update", "Delete"])
    branches = ops.list_branches()

    with t[0]:
        show_table(ops.list_employees(), ["Employee ID", "Name", "Role", "Salary", "Branch"])

    with t[1]:
        if not branches:
            st.warning("Add a branch first.")
        else:
            with st.form("emp_add"):
                name = st.text_input("Name", key="emp_add_name")
                role = st.text_input("Role", key="emp_add_role")
                salary = st.number_input("Salary", min_value=0.0, format="%.2f", key="emp_add_salary")
                bid = pick("Branch", branches, "emp_add_branch")
                ok = st.form_submit_button("Add employee")
            if ok:
                run(lambda: ops.add_employee(req(name, "Name"), req(role, "Role"), salary, bid),
                    "Employee added.")

    with t[2]:
        rows = ops.list_employees()
        if not rows:
            st.info("No employees yet.")
        else:
            eid = pick("Employee", rows, "emp_upd_pick")
            rec = ops.get_employee(eid)
            with st.form("emp_upd"):
                name = st.text_input("Name", value=rec[1], key=f"emp_upd_name_{eid}")
                role = st.text_input("Role", value=rec[2], key=f"emp_upd_role_{eid}")
                salary = st.number_input("Salary", min_value=0.0, value=float(rec[3]),
                                         format="%.2f", key=f"emp_upd_salary_{eid}")
                bid = pick("Branch", branches, f"emp_upd_branch_{eid}", current=rec[4])
                ok = st.form_submit_button("Update employee")
            if ok:
                run(lambda: ops.update_employee(eid, req(name, "Name"), req(role, "Role"),
                                                salary, bid), "Employee updated.")

    with t[3]:
        delete_block("emp", ops.list_employees(), lambda r: r[1], ops.delete_employee, "Employee",
                     "An employee who has sales cannot be deleted.")


# ---------------------------------------------------- Supplier (new table)
def page_suppliers():
    st.header("Suppliers")
    t = st.tabs(["List", "Add", "Update", "Delete"])
    medicines = ops.list_medicines()

    with t[0]:
        st.caption("LEFT JOIN (book Example 28): suppliers without a medicine also appear.")
        show_table(ops.list_all_suppliers(),
                   ["Supplier ID", "Name", "Phone", "Address", "Medicine"])

    with t[1]:
        with st.form("sup_add"):
            name = st.text_input("Name", key="sup_add_name")
            phone = st.text_input("Phone", key="sup_add_phone")
            addr = st.text_input("Address", key="sup_add_addr")
            mid = pick("Medicine supplied", medicines, "sup_add_med", allow_none=True)
            ok = st.form_submit_button("Add supplier")
        if ok:
            run(lambda: ops.add_supplier(req(name, "Name"), clean_text(phone),
                                         clean_text(addr), mid), "Supplier added.")

    with t[2]:
        rows = ops.list_all_suppliers()
        if not rows:
            st.info("No suppliers yet.")
        else:
            sid = pick("Supplier", rows, "sup_upd_pick")
            rec = ops.get_supplier(sid)
            with st.form("sup_upd"):
                name = st.text_input("Name", value=rec[1], key=f"sup_upd_name_{sid}")
                phone = st.text_input("Phone", value=rec[2] or "", key=f"sup_upd_phone_{sid}")
                addr = st.text_input("Address", value=rec[3] or "", key=f"sup_upd_addr_{sid}")
                mid = pick("Medicine supplied", medicines, f"sup_upd_med_{sid}",
                           current=rec[4], allow_none=True)
                ok = st.form_submit_button("Update supplier")
            if ok:
                run(lambda: ops.update_supplier(sid, req(name, "Name"), clean_text(phone),
                                                clean_text(addr), mid), "Supplier updated.")

    with t[3]:
        delete_block("sup", ops.list_all_suppliers(), lambda r: r[1], ops.delete_supplier, "Supplier")


# --------------------------------------------------------------- Inventory
def page_inventory():
    st.header("Inventory")
    t = st.tabs(["List", "Add batch", "Update batch", "Delete batch"])
    branches = ops.list_branches()
    medicines = ops.list_medicines()

    with t[0]:
        show_table(ops.list_inventory(),
                   ["Inventory ID", "Batch", "Medicine", "Quantity", "Expiry", "Branch"])

    with t[1]:
        if not branches or not medicines:
            st.warning("Add a branch and a medicine first.")
        else:
            with st.form("inv_add"):
                batch = st.text_input("Batch number", key="inv_add_batch")
                qty = st.number_input("Quantity", min_value=0, step=1, key="inv_add_qty")
                expiry = st.date_input("Expiry date", value=datetime.date.today(), key="inv_add_exp")
                bid = pick("Branch", branches, "inv_add_branch")
                mid = pick("Medicine", medicines, "inv_add_med")
                ok = st.form_submit_button("Add batch")
            if ok:
                run(lambda: ops.add_batch(req(batch, "Batch number"), int(qty), expiry, bid, mid),
                    "Batch added.")

    inv_label = lambda r: f"{r[1]} ({r[2]})"

    with t[2]:
        rows = ops.list_inventory()
        if not rows:
            st.info("No batches yet.")
        else:
            iid = pick("Batch", rows, "inv_upd_pick", label_fn=inv_label)
            rec = ops.get_inventory(iid)
            with st.form("inv_upd"):
                batch = st.text_input("Batch number", value=rec[1], key=f"inv_upd_batch_{iid}")
                qty = st.number_input("Quantity", min_value=0, value=int(rec[2]), step=1,
                                      key=f"inv_upd_qty_{iid}")
                expiry = st.date_input("Expiry date", value=rec[3], key=f"inv_upd_exp_{iid}")
                bid = pick("Branch", branches, f"inv_upd_branch_{iid}", current=rec[4])
                mid = pick("Medicine", medicines, f"inv_upd_med_{iid}", current=rec[5])
                ok = st.form_submit_button("Update batch")
            if ok:
                run(lambda: ops.update_batch(iid, req(batch, "Batch number"), int(qty),
                                             expiry, bid, mid), "Batch updated.")

    with t[3]:
        delete_block("inv", ops.list_inventory(), inv_label, ops.delete_batch, "Batch")


# --------------------------------------------------------------- Purchases
def page_purchases():
    st.header("Purchases")
    t = st.tabs(["List", "New purchase", "Update", "Delete"])
    medicines = ops.list_medicines()
    pur_label = lambda r: f"{r[1]} - total {r[2]:.2f}"

    with t[0]:
        rows = ops.list_purchases()
        show_table(rows, ["Purchase ID", "Date", "Total Cost"])
        if rows:
            pid = pick("Show lines of purchase", rows, "pur_show", label_fn=pur_label)
            show_table(ops.purchase_lines(pid), ["Medicine", "Quantity"])

    with t[1]:
        if not medicines:
            st.warning("Add a medicine first.")
        else:
            n = st.number_input("Number of medicine lines", min_value=1, max_value=10,
                                value=1, step=1, key="pur_add_n")
            with st.form("pur_add"):
                pdate = st.date_input("Purchase date", value=datetime.date.today(), key="pur_add_date")
                total = st.number_input("Total cost", min_value=0.0, format="%.2f", key="pur_add_total")
                lines = collect_lines("pur_add", n, medicines)
                ok = st.form_submit_button("Save purchase")
            if ok:
                run(lambda: ops.create_purchase(pdate, total, lines),
                    lambda pid: f"Purchase #{pid} saved.")

    with t[2]:
        rows = ops.list_purchases()
        if not rows:
            st.info("No purchases yet.")
        else:
            pid = pick("Purchase", rows, "pur_upd_pick", label_fn=pur_label)
            rec = ops.get_purchase(pid)
            with st.form("pur_upd"):
                pdate = st.date_input("Purchase date", value=rec[1], key=f"pur_upd_date_{pid}")
                total = st.number_input("Total cost", min_value=0.0, value=float(rec[2]),
                                        format="%.2f", key=f"pur_upd_total_{pid}")
                ok = st.form_submit_button("Update purchase")
            if ok:
                run(lambda: ops.update_purchase(pid, pdate, total), "Purchase updated.")

    with t[3]:
        delete_block("pur", ops.list_purchases(), pur_label, ops.delete_purchase, "Purchase",
                     "The purchase lines are deleted with it.")


# ---------------------------------------------------------------- New Sale
def page_new_sale():
    st.header("New Sale")
    customers = ops.list_customers()
    employees = ops.list_employees()
    medicines = ops.list_medicines()

    if not (customers and employees and medicines):
        st.warning("You need at least one customer, one employee and one medicine.")
        return

    # outside the form: widgets inside a form do not update until submit
    n = st.number_input("Number of medicine lines", min_value=1, max_value=10,
                        value=1, step=1, key="sale_n")

    with st.form("sale_form"):
        cid = pick("Customer", customers, "sale_cus")
        eid = pick("Employee", employees, "sale_emp")
        pay = st.selectbox("Payment method", PAYMENT_METHODS, key="sale_pay")
        lines = collect_lines("sale", n, medicines)
        st.markdown("**Prescription (optional)** - created only if the doctor name is filled in")
        doctor = st.text_input("Doctor name", key="sale_doc")
        diagnosis = st.text_input("Diagnosis", key="sale_diag")
        ok = st.form_submit_button("Save sale")

    if ok:
        run(lambda: ops.create_sale(cid, eid, pay, lines, clean_text(doctor), clean_text(diagnosis)),
            lambda r: f"Sale #{r[0]} saved. Amount: {r[1]:.2f}")


# ------------------------------------------------------------------- Sales
def page_sales():
    st.header("Sales")
    t = st.tabs(["All sales", "Update", "Delete"])
    sale_label = lambda r: f"{r[1]} - {r[2]} - {r[5]:.2f}"

    with t[0]:
        rows = ops.list_sales()
        show_table(rows, ["Sale ID", "Date", "Customer", "Employee", "Payment", "Amount"])
        if rows:
            sid = pick("Show details of sale", rows, "sale_show", label_fn=sale_label)
            st.write("Medicines in this sale:")
            show_table(ops.sale_lines(sid), ["Medicine", "Price", "Quantity", "Line Total"])
            st.write("Prescription:")
            show_table(ops.sale_prescription(sid),
                       ["Prescription ID", "Doctor", "Diagnosis", "Date"])

    with t[1]:
        rows = ops.list_sales()
        if not rows:
            st.info("No sales yet.")
        else:
            sid = pick("Sale", rows, "sale_upd_pick", label_fn=sale_label)
            rec = ops.get_sale(sid)
            customers = ops.list_customers()
            employees = ops.list_employees()
            with st.form("sale_upd"):
                cid = pick("Customer", customers, f"sale_upd_cus_{sid}", current=rec[4])
                eid = pick("Employee", employees, f"sale_upd_emp_{sid}", current=rec[5])
                pay = st.selectbox("Payment method", PAYMENT_METHODS,
                                   index=PAYMENT_METHODS.index(rec[3]) if rec[3] in PAYMENT_METHODS else 0,
                                   key=f"sale_upd_pay_{sid}")
                ok = st.form_submit_button("Update sale")
            if ok:
                run(lambda: ops.update_sale(sid, cid, eid, pay), "Sale updated.")

    with t[2]:
        delete_block("sale", ops.list_sales(), sale_label, ops.delete_sale, "Sale",
                     "The sale's medicine lines and prescription are deleted with it.")


# ------------------------------------------------------------ Prescriptions
def page_prescriptions():
    st.header("Prescriptions")
    t = st.tabs(["List", "Add", "Update", "Delete"])
    presc_label = lambda r: f"Dr. {r[1]} ({r[3]})"

    with t[0]:
        show_table(ops.list_prescriptions(),
                   ["Prescription ID", "Doctor", "Diagnosis", "Date", "Sale ID", "Customer"])

    with t[1]:
        sales = ops.list_sales()
        if not sales:
            st.warning("Record a sale first.")
        else:
            with st.form("presc_add"):
                doctor = st.text_input("Doctor name", key="presc_add_doc")
                diagnosis = st.text_input("Diagnosis", key="presc_add_diag")
                pdate = st.date_input("Date", value=datetime.date.today(), key="presc_add_date")
                sid = pick("Sale", sales, "presc_add_sale",
                           label_fn=lambda r: f"{r[1]} - {r[2]} - {r[5]:.2f}")
                ok = st.form_submit_button("Add prescription")
            if ok:
                run(lambda: ops.add_prescription(req(doctor, "Doctor name"), clean_text(diagnosis),
                                                 pdate, sid), "Prescription added.")

    with t[2]:
        rows = ops.list_prescriptions()
        if not rows:
            st.info("No prescriptions yet.")
        else:
            pid = pick("Prescription", rows, "presc_upd_pick", label_fn=presc_label)
            rec = ops.get_prescription(pid)
            with st.form("presc_upd"):
                doctor = st.text_input("Doctor name", value=rec[1], key=f"presc_upd_doc_{pid}")
                diagnosis = st.text_input("Diagnosis", value=rec[2] or "", key=f"presc_upd_diag_{pid}")
                pdate = st.date_input("Date", value=rec[3], key=f"presc_upd_date_{pid}")
                ok = st.form_submit_button("Update prescription")
            if ok:
                run(lambda: ops.update_prescription(pid, req(doctor, "Doctor name"),
                                                    clean_text(diagnosis), pdate),
                    "Prescription updated.")

    with t[3]:
        delete_block("presc", ops.list_prescriptions(), presc_label,
                     ops.delete_prescription, "Prescription")


# ----------------------------------------------------------------- Reports
def page_reports():
    st.header("Reports")

    n, max_p, min_p, avg_p = ops.rep_medicine_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Medicines", n)
    c2.metric("Highest price", f"{(max_p or 0):.2f}")
    c3.metric("Lowest price", f"{(min_p or 0):.2f}")
    c4.metric("Average price", f"{(avg_p or 0):.2f}")

    tabs = st.tabs([
        "Sales detail", "Sold per medicine", "HAVING", "Per employee",
        "Per payment", "Branch staff", "Branch stock", "Expiring",
        "Subqueries",
    ])
    with tabs[0]:
        st.caption("Five-table join: Sale, Customer, Employee, Sale_Medicine, Medicine")
        show_table(ops.rep_sales_detail(),
                   ["Sale ID", "Date", "Customer", "Employee", "Medicine", "Quantity"])
    with tabs[1]:
        st.caption("GROUP BY with SUM (book Q10)")
        show_table(ops.rep_sold_per_medicine(), ["Medicine ID", "Medicine", "Total Sold"])
    with tabs[2]:
        st.caption("Medicines sold in more than one sale (HAVING COUNT > 1, book Q11)")
        show_table(ops.rep_sold_more_than_once(), ["Medicine ID", "Medicine", "Number of Sales"])
    with tabs[3]:
        st.caption("COUNT, SUM, AVG, MAX, MIN per employee")
        show_table(ops.rep_sales_per_employee(),
                   ["Employee ID", "Employee", "Sales", "Total", "Average", "Max", "Min"])
    with tabs[4]:
        st.caption("Sales per payment method")
        show_table(ops.rep_sales_per_payment(), ["Payment", "Sales", "Total", "Average"])
    with tabs[5]:
        st.caption("Employees and total salaries per branch")
        show_table(ops.rep_branch_staff(),
                   ["Branch ID", "Branch", "Employees", "Total Salaries"])
    with tabs[6]:
        st.caption("Batches and total quantity per branch")
        show_table(ops.rep_branch_stock(),
                   ["Branch ID", "Branch", "Batches", "Total Quantity"])
    with tabs[7]:
        st.caption("Batches expiring before a date (comparison operator <)")
        d = st.date_input("Expiring before", value=datetime.date.today() + datetime.timedelta(days=180),
                          key="rep_exp_date")
        show_table(ops.rep_expiring(d),
                   ["Inventory ID", "Batch", "Medicine", "Quantity", "Expiry", "Branch"])
    with tabs[8]:
        st.caption("Medicines priced above the average (scalar subquery)")
        show_table(ops.rep_medicines_above_average(), ["Medicine ID", "Medicine", "Price"])
        st.caption("Medicines never purchased (NOT IN subquery)")
        show_table(ops.rep_medicines_never_purchased(), ["Medicine ID", "Medicine", "Price"])
        st.caption("Customers without sales (NOT IN subquery)")
        show_table(ops.rep_customers_without_sales(), ["Customer ID", "Name", "Phone"])


# -------------------------------------------------------------------- Menu
PAGES = {
    "Branches": page_branches,
    "Medicines": page_medicines,
    "Customers": page_customers,
    "Employees": page_employees,
    "Suppliers": page_suppliers,
    "Inventory": page_inventory,
    "Purchases": page_purchases,
    "New Sale": page_new_sale,
    "Sales": page_sales,
    "Prescriptions": page_prescriptions,
    "Reports": page_reports,
    "Products - View / Search": page_products_view,
    "Products - Add": page_products_add,
    "Products - Update": page_products_update,
    "Products - Delete": page_products_delete,
    "Products - Reports": page_products_reports,
}

menu = st.sidebar.selectbox("Choose an action", list(PAGES))
PAGES[menu]()