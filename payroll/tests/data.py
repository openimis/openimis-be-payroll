gql_payment_point_query = """
query q1 {
  paymentPoint {
    edges {
      node {
        id
      }
    }
  }
}
"""

gql_payment_point_filter = """
query q1 {
  paymentPoint(name_Iexact: "%s", location_Uuid: "%s", ppm_Uuid: "%s") {
    edges {
      node {
        id
      }
    }
  }
}
"""

gql_payment_point_create = """
mutation m1 {
  createPaymentPoint (input:{
    name: %s,
    locationId: %s,
    ppmId: "%s"
  }) {
    clientMutationId
  }
}
"""

gql_payment_point_update = """
mutation m1 {
  updatePaymentPoint (input:{
    id: %s
    name: %s,
    locationId: %s,
    ppmId: "%s"
  }) {
    clientMutationId
  }
}
"""

gql_payment_point_delete = """
mutation m1 {
  deletePaymentPoint (input:{
    ids: %s
  }) {
    clientMutationId
  }
}
"""

gql_payroll_query = """
query q2 {
  payroll {
    edges {
      node {
        id
      }
    }
  }
}
"""

gql_payroll_filter = """
query q2 {
  paymentPoint(name_Iexact: "%s", 
                benefitPlan_Uuid: "%s", 
                paymentPoint_Uuid: "%s"
                dateValidFrom: "%s"
                dateValidTo: "%s") {
    edges {
      node {
        id
      }
    }
  }
}
"""

gql_payroll_create = """
mutation m2 {
  createPayroll (input:{
                name: "%s", 
                benefitPlanId: "%s", 
                paymentPointId: "%s"
                paymentMethod: "%s"
                status: %s
                dateValidFrom: "%s"
                dateValidTo: "%s"
                jsonExt: "%s"
  }) {
    clientMutationId
  }
}
"""

gql_payroll_create_no_json_ext = """
mutation m2 {
  createPayroll (input:{
                name: "%s", 
                benefitPlanId: "%s", 
                paymentPointId: "%s"
                paymentMethod: "%s"
                status: %s
                dateValidFrom: "%s"
                dateValidTo: "%s"
  }) {
    clientMutationId
  }
}
"""


gql_payroll_delete = """
mutation m2 {
  deletePayroll (input:{
    ids: %s
  }) {
    clientMutationId
  }
}
"""
