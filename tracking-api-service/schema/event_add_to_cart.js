cube(`EventAddToCart`, {
  sql: `SELECT * FROM tracking_problem.event_add_to_cart`,

  measures: {
    count: {
      type: `count`,
      drillMembers: [session_id, user_id, productName, timestamp],
    },

    totalQuantity: {
      sql: `quantity`,
      type: `sum`,
    },

    totalRevenue: {
      sql: `totalValue`,
      type: `sum`,
    },

    avgProductPrice: {
      sql: `productPrice`,
      type: `avg`,
    },
  },

  dimensions: {
    session_id: {
      sql: `session_id`,
      type: `string`,
    },

    user_id: {
      sql: `user_id`,
      type: `string`,
    },

    event_type: {
      sql: `event_type`,
      type: `string`,
    },

    productName: {
      sql: `productName`,
      type: `string`,
    },

    productBrand: {
      sql: `productBrand`,
      type: `string`,
    },

    productPrice: {
      sql: `productPrice`,
      type: `number`,
    },

    quantity: {
      sql: `quantity`,
      type: `number`,
    },

    totalValue: {
      sql: `totalValue`,
      type: `number`,
    },

    timestamp: {
      sql: `timestamp`,
      type: `time`,
    },
  }
});
