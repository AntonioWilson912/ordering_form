$(document).ready(function () {
  console.log("Product form script loaded.");

  // Hide initial banner
  $(".banner").hide();
  $(".form-error").hide();

  $("#newProductForm").submit(function (e) {
    e.preventDefault();

    $.ajax({
      type: "POST",
      url: "/api/products/create/",
      data: {
        company_id: $("#companySelect").val(),
        name: $("input[name='name']").val(),
        item_no: $("input[name='item_no']").val(),
        item_type: $("select[name='item_type']").val(),
        csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      },
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      success: function (data) {
        if (data.success === false && data.errors) {
          showBanner("Please correct the errors below.", "warning");

          // Show specific field errors
          $(".form-error").hide();

          if (data.errors.company_id_error) {
            $("#companyError").text(data.errors.company_id_error).show();
          }
          if (data.errors.name_error) {
            $("#nameError").text(data.errors.name_error).show();
          }
          if (data.errors.item_no_error) {
            $("#itemNoError").text(data.errors.item_no_error).show();
          }
          if (data.errors.item_type_error) {
            $("#itemTypeError").text(data.errors.item_type_error).show();
          }
        } else if (data.success) {
          showBanner("Your product was created successfully.", "success");
          $("#newProductForm").trigger("reset");
          $(".form-error").hide();

          setTimeout(function () {
            window.location.href = PRODUCT_LIST_URL;
          }, 1500);
        }
      },
      error: function (xhr) {
        console.error("Error response:", xhr);
        const errorData = xhr.responseJSON;

        if (errorData && errorData.errors) {
          showBanner("Please correct the errors below.", "warning");

          $(".form-error").hide();

          if (errorData.errors.company_id_error) {
            $("#companyError").text(errorData.errors.company_id_error).show();
          }
          if (errorData.errors.name_error) {
            $("#nameError").text(errorData.errors.name_error).show();
          }
          if (errorData.errors.item_no_error) {
            $("#itemNoError").text(errorData.errors.item_no_error).show();
          }
          if (errorData.errors.item_type_error) {
            $("#itemTypeError").text(errorData.errors.item_type_error).show();
          }
        } else {
          const errorMsg = errorData?.message || "An error occurred";
          showBanner(errorMsg, "warning");
        }
      },
    });
  });
});
