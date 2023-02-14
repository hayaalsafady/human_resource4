# Copyright (c) 2023, GSG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class leaveAllocation(Document):
    def validate(self):
        self.validate_dates()
        self.check_for_duplication()

    def validate_dates(self):
        if self.to_date < self.from_date:
            frappe.throw("To Date should be a date after From Date ")

    def check_for_duplication(self):
        leave_file = frappe.db.sql(""" select * from `tabLeaveAllocation` where from_date between %s and %s 
		and to_date between %s and %s and employee = %s and leave_type = %s """, (
            self.from_date, self.to_date, self.from_date, self.to_date, self.employee, self.leave_type), as_dict=1)

        if leave_file:
            frappe.throw("This leave allocation already exists!")
