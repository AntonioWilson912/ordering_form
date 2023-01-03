$(document).ready(function() {
    console.log("Product form script loaded.");
    $("#bannerClose").click(function() {
        $("#banner").hide();
    });
    $("#banner").hide();

    $("#newProductForm").submit(function(e) {
        e.preventDefault();
        console.log("Form submitted.");
        $.ajax({
            type: "POST",
            url: "/products/create",
            data: {
                company_id: $("#companySelect").val(),
                name: $("input[name='name']").val(),
                item_no: $("input[name='item_no']").val(),
                item_type: $("select[name='item_type']").val(),
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                dataType: "json"
            },
            success: function(data) {
                if ("errors" in data) {
                    $("#banner").addClass("banner-warning").removeClass("banner-success").show();
                    $("#bannerText").text("There was an error with your new product submission.");
                    if ("company_error" in data.errors)
                        $("#companyError").text(data.errors["company_error"]).show();
                    else
                        $("#companyError").hide();

                    if ("name_error" in data.errors)
                        $("#nameError").text(data.errors["name_error"]).show();
                    else
                        $("#nameError").hide();

                    if ("item_no_error" in data.errors)
                        $("#itemNoError").text(data.errors["item_no_error"]).show();
                    else
                        $("#itemNoError").hide();

                    if ("item_type_error" in data.errors)
                        $("#itemTypeError").text(data.errors["item_type_error"]).show();
                    else
                        $("#itemTypeError").hide();
                }
                else {
                    $("#banner").addClass("banner-success").removeClass("banner-warning").show();
                    $("#bannerText").text("Your product was created successfully.");
                    $("#newProductForm").trigger("reset");
                    $(".form-error").hide();
                }
            },
            error: function(errorMessage) {
                console.log(errorMessage);
            }
        });
    });
});