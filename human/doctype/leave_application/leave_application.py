# Copyright (c) 2023, GSG and contributors
# For license information, please see license.txt
from datetime import datetime

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff


def get_today():
    today = datetime.now().strftime("%Y-%m-%d")
    return today


class Leaveapplication(Document):

    def validate(self):
        self.set_total_leave_day()
        self.get_total_leaves_allocated()
        self.check_leave_balance()
        self.validate_from_date()
        self.validate_dates()
        self.check_for_duplication()
        self.check_max_days()
        self.validate_alternative_employee()

    def on_submit(self):
        self.update_balance_allocation_after_submit()

    def on_cancel(self):
        self.update_balance_allocation_after_cancel()

    # TEST

    def set_total_leave_day(self):
        if self.to_date and self.from_date:
            total_leave_day = date_diff(self.to_date, self.from_date) + 1
            if total_leave_day >= 0:
                self.total_leave_day = total_leave_day

    def get_total_leaves_allocated(self):
        if self.employee and self.from_date and self.to_date and self.leave_type:
            leaves_allocated = frappe.db.sql(""" select total_leaves_allocated from `tableave Allocation`
			where employee = %s and leave_type = %s and from_date <= %s and to_date >= %s""",
											 (self.employee, self.leave_type, self.from_date, self.to_date), as_dict=1)

            if leaves_allocated:
				self.leave_balance_before_application = str(leaves_allocated[0].total_leaves_allocated)


    def check_leave_balance(self):
        negative_balance = frappe.db.sql(""" select negative_balance from `tabLeave Type` 
                where leave_type_name = %s""", (self.leave_type))

        if self.total_leave_days and self.leave_balance_before_application:
            if float(self.total_leave_days) > float(self.leave_balance_before_application) and negative_balance[0][0] == 0:
                frappe.throw("not have balance for leave type " + self.leave_type)

    def update_balance_allocation_after_submit(self):
        new_balance_allocation = float(self.leave_balance_before_application) - self.total_leave_day
        frappe.db.sql(""" update `tabLeave Allocation`  set  total_leaves_allocated = %s 
	        where employee = %s and leave_type = %s and from_date <= %s 
	        and to_date >= %s""",
                      (new_balance_allocation, self.employee, self.leave_type, self.from_date, self.to_date),
                      as_dict=1)

        frappe.db.commit

    def update_balance_allocation_after_cancel(self):
        leaves_allocated = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` 
	            where employee = %s and leave_type = %s and from_date <= %s and to_date >= %s""",
                                         (self.employee, self.leave_type, self.from_date, self.to_date), as_dict=1)

        if leaves_allocated:
            self.leave_balance_before_application = str(leaves_allocated[0].total_leaves_allocated)

        new_balance_allocation = float(self.leave_balance_before_application) - self.total_leave_days
        frappe.db.sql(""" update 'tabLeave Allocation2' set  total_leaves_allocated = %s 
	        where employee = %s and leave_type = %s and from_date <= %s 
	        and to_date >= %s""",
                      (new_balance_allocation, self.employee, self.leave_type, self.from_date, self.to_date),
                      as_dict=1)

        frappe.db.commit

    def validate_from_date(self):
        if self.from_date < get_today():
            frappe.throw("FromDate can not be before today's date!")

    def validate_dates(self):
        if self.to_date < self.from_date:
            frappe.throw("To Date should be a date after From Date ")

    def check_for_duplication(self):
        leave_file = frappe.db.sql(""" select * from `tabLeave Application ` where from_date between %s and %s 
	        and to_date between %s and %s and employee = %s and leave_type = %s """, (
            self.from_date, self.to_date, self.from_date, self.to_date, self.employee, self.leave_type),
                                   as_dict=1)
        if leave_file:
            frappe.throw("This leave application already exists!")

    def check_max_days(self):
        max_days = frappe.db.sql(""" select s,max_day negative_balance from `tabLeave Type` 
	        where leave_type_name = %s""", (self.leave_type))

        if self.total_leave_days > max_days[0][0] and max_days[0][1] == 0:
            frappe.throw("Max Continuous Days Allowed for this leave type is " + str(max_days[0][0]))

    def validate_applicable_after(self):
        applicable_after = frappe.db.sql(""" select applicable_after from `tabLeave Type` 
	        where leave_type_name = %s""", (self.leave_type))

        diff = date_diff(get_today(), self.from_date)

        if diff < int(applicable_after[0][0]):
            frappe.throw("You have to apply for this leave type at least " + str(applicable_after[0][0]) +
                         " days in advance.")

    def validate_alternative_employee(self):
        if self.employee == self.alternative_employee:
            frappe.throw("Please choose another alternative employee")
