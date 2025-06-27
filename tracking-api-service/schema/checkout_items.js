cube(`CheckoutItems`, {
  sql: `SELECT * FROM tracking_problem.checkout_items`,

  // 👇 THÊM refreshKey TẠI ĐÂY
  refreshKey: {
    sql: `SELECT MAX(timestamp) FROM tracking_problem.checkout_items`
  },

  measures: {
    count: {
      type: `count`,
      drillMembers: [session_id, user_id, product_name, timestamp],
    },

    totalQuantity: {
      sql: `quantity`,
      type: `sum`,
    },

    totalRevenue: {
      sql: `product_price * quantity`,
      type: `sum`,
      // 👈 tính tổng doanh thu từ giá * số lượng
    },

    avgProductPrice: {
      sql: `product_price`,
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

    product_name: {
      sql: `product_name`,
      type: `string`,
    },

    product_brand: {
      sql: `product_brand`,
      type: `string`,
    },

    product_price: {
      sql: `product_price`,
      type: `number`,
    },

    quantity: {
      sql: `quantity`,
      type: `number`,
    },

    timestamp: {
      sql: `timestamp`,
      type: `time`,
    },
  }
});
