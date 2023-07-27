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
    ppmId: %s
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
    ppmId: %s
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
