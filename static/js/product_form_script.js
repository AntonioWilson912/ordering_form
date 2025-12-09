$(document).ready(function () {
  console.log("Product form script loaded.");

  $("#bannerClose").click(function () {
    $("#banner").hide();
  });

  $("#banner").hide();
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
          // Show banner with general error
          $("#banner")
            .addClass("banner-warning")
            .removeClass("banner-success")
            .show();
          $("#bannerText").text("Please correct the errors below.");

          // Show specific field errors
          $(".form-error").hide(); // Hide all errors first

          if (data.errors.company_error) {
            $("#companyError").text(data.errors.company_error).show();
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

          // Scroll to banner
          $("html, body").animate(
            {
              scrollTop: $("#banner").offset().top - 100,
            },
            300
          );
        } else if (data.success) {
          $("#banner")
            .addClass("banner-success")
            .removeClass("banner-warning")
            .show();
          $("#bannerText").text("Your product was created successfully.");
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
          // Handle validation errors
          $("#banner")
            .addClass("banner-warning")
            .removeClass("banner-success")
            .show();
          $("#bannerText").text("Please correct the errors below.");

          $(".form-error").hide();

          if (errorData.errors.company_error) {
            $("#companyError").text(errorData.errors.company_error).show();
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
          // Generic error
          const errorMsg = errorData?.message || "An error occurred";
          $("#banner")
            .addClass("banner-warning")
            .removeClass("banner-success")
            .show();
          $("#bannerText").text(errorMsg);
        }

        $("html, body").animate(
          {
            scrollTop: $("#banner").offset().top - 100,
          },
          300
        );
      },
    });
  });
});
