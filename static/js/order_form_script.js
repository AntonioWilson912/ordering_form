$(document).ready(function () {
  console.log("Order form script loaded.");

  $("#bannerClose").click(function () {
    $("#banner").hide();
  });

  $("#banner").hide();

  // Company selection handler
  $("#companySelect").change(function (e) {
    e.preventDefault();

    const companyId = $(this).val();

    if (companyId === "-1") {
      $("#productForm").hide();
      $("#newOrderSubmit").hide();
      return;
    }

    // Fetch products for selected company
    $.ajax({
      type: "POST",
      url: `/api/products/company/${companyId}/`,
      data: {
        csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      },
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      success: function (data) {
        if (!data.success) {
          showBanner(data.message, "warning");
          $("#productForm").hide();
          $("#newOrderSubmit").hide();
          return;
        }

        renderProductTable(data.company_name, data.products);
        $("#newOrderSubmit").show();
        $("#companySelectGroup").hide();
        $("#banner").hide();
      },
      error: function (xhr) {
        const errorMsg = xhr.responseJSON?.message || "An error occurred";
        showBanner(errorMsg, "warning");
        $("#productForm").hide();
        $("#newOrderSubmit").hide();
      },
    });
  });

  // Form submission handler
  $("#newOrderForm").submit(function (e) {
    e.preventDefault();

    // Collect product quantities
    const orderData = {
      csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
    };

    let hasItems = false;
    $("input[name^='product_']").each(function () {
      const quantity = parseInt($(this).val());
      if (quantity > 0) {
        orderData[$(this).attr("name")] = quantity;
        hasItems = true;
      }
    });

    if (!hasItems) {
      showBanner(
        "Please select at least one product with quantity > 0",
        "warning"
      );
      return;
    }

    // Submit order
    $.ajax({
      type: "POST",
      url: "/api/orders/create/",
      data: orderData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      success: function (data) {
        if (data.success) {
          showBanner(data.message, "success");
          setTimeout(function () {
            window.location.href = ORDER_LIST_URL;
          }, 1500);
        } else {
          showBanner(data.message, "warning");
        }
      },
      error: function (xhr) {
        const errorMsg = xhr.responseJSON?.message || "An error occurred";
        showBanner(errorMsg, "warning");
      },
    });
  });

  // Helper function to render product table
  function renderProductTable(companyName, products) {
    let html = `
            <table class="table table-striped">
                <caption>New Order for ${companyName}</caption>
                <thead>
                    <tr>
                        <th>Item No.</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody>
        `;

    products.forEach((product) => {
      const itemType = product.item_type === "W" ? "Weight" : "Case";
      html += `
                <tr>
                    <td>${product.item_no || "N/A"}</td>
                    <td>${product.name}</td>
                    <td>${itemType}</td>
                    <td>
                        <input type="number"
                               name="product_${product.id}"
                               id="product_${product.id}"
                               value="0"
                               min="0"
                               class="form-control quantity-input">
                    </td>
                </tr>
            `;
    });

    html += `
                </tbody>
            </table>
        `;

    $("#productForm").html(html).show();
  }

  // Helper function to show banner messages
  function showBanner(message, type) {
    $("#bannerText").text(message);
    $("#banner")
      .removeClass("banner-success banner-warning")
      .addClass(`banner-${type}`)
      .show();

    // Scroll to banner
    $("html, body").animate(
      {
        scrollTop: $("#banner").offset().top - 100,
      },
      300
    );
  }
});
