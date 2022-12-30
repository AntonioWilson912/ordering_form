$(document).ready(function() {
    console.log("Form script loaded.");
    $("#newOrderSubmit").hide();
    $("#bannerClose").click(function() {
        $("#banner").hide();
    });
    $("#banner").hide();
    $("#companySelect").change(function(e) {
        e.preventDefault();
        console.log("Current value of companySelect is", $("#companySelect").val());
        $.ajax({
            type: "POST",
            url: "/products/orders/company/get_products",
            data: {
                company_id: $("#companySelect").val(),
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                dataType: "json"
            },
            success: function(data) {
                console.log("Here's what we got:", data);
                if (!data.company_products) {
                    $("#newOrderSubmit").hide();
                    $("#productForm").hide();
                    $("#banner").addClass("banner-warning");
                    $("#bannerText").text(data.company_error)
                    $("#banner").show();
                }
                else {
                    var productTable = `
                        <table class="table table-striped">
                            <caption>New Order for ${data.company_name}</caption>
                            <thead>
                                <tr>
                                    <th>Item No.</th>
                                    <th>Name</th>
                                    <th>Item Type</th>
                                    <th>Qty</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    var products = data.company_products;
                    for (var i = 0; i < products.length; i++) {
                        productTable += `
                            <tr>
                                <td>${products[i].item_no}</td>
                                <td>${products[i].name}</td>
                                <td>
                        `;
                        if (products[i].item_type == 'W')
                            productTable += "Weight";
                        else
                            productTable += "Case";

                        productTable += `
                                </td>
                                <td><input type="number" id="product${products[i].id}" name="product${products[i].id}" value="0"></td>
                            </tr>
                        `;
                    }
                    productTable += `
                        </tbody>
                    </table>
                    `;

                    $("#newOrderSubmit").show();
                    $("#productForm").html(productTable);
                    $("#productForm").show();
                    $("#banner").removeClass("banner-warning");
                    $("#companySelectGroup").hide();
                    $("#banner").hide();
                }
            },
            error: function(errorMessage) {
                console.log(errorMessage);
            }
        });
    });
    $("#newOrderForm").submit(function(e) {
        e.preventDefault();
        // Let's just test to see if we can get all the values of the input fields
        var formInputs = $(this).serializeArray();
        var productsToSend = formInputs.filter(input => input.value > 0 && input.name.startsWith("product"));
        productsToSend.forEach(input => console.log(input));
        $.ajax({
            type: "POST",
            url: "/products/orders/create",
            data: {
                ordered_products: productsToSend,
                csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                dataType: "json"
            },
            success: function(data) {
                console.log("Order submision was a success.");
                console.log(data);
            },
            error: function(errorMessage) {
                console.log(errorMessage);
            }
        });
    });
});