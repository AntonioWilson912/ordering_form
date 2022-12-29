var rotation = 0;

jQuery.fn.rotate = function(degrees) {
    $(this).css({"-webkit-transform": "rotate(" + degrees + "deg)",
        "-moz-transform": "rotate(" + degrees + "deg)",
        "-ms-transform": "rotate(" + degrees + "deg)",
        "transform": "rotate(" + degrees + "deg)"
    });

    return $(this);
}

$(document).ready(function() {
    console.log("JavaScript has officially loaded.");

    $("#toggle-sidebar-btn").click(function(e) {
        rotation = (rotation == 0) ? 180 : 0;
        $("#toggle-sidebar").rotate(rotation);

        if ($("#sidebar").css("flex") == "2 1 0%") {
            $("#sidebar").css("flex", "1 1 0%");
            $("#content").css("flex", "11 1 0%");
            $("#sidebar .header h2").hide();
            $("#sidebar .header strong").show();
            $("#sidebar ul li span").hide();
            $("#sidebar ul li").css("text-align", "center");
            $("#sidebar ul li .fa-solid, #sidebar ul li .fa-regular").css("margin-right", "0");
        }
        else {
            $("#sidebar").css("flex", "2 1 0%");
            $("#content").css("flex", "10 1 0%");
            $("#sidebar .header h2").show();
            $("#sidebar .header strong").hide();
            $("#sidebar ul li span").show();
            $("#sidebar ul li").css("text-align", "inherit");
            $("#sidebar ul li .fa-solid, #sidebar ul li .fa-regular").css("margin-right", "10px");
        }
    });

    $("#user-icon").click(function() {
        var chevronClassList = $("#user-icon-chevron").attr("class");
        var chevronClassArr = chevronClassList.split(" ");
        if (chevronClassArr.indexOf("fa-chevron-down") != -1) {
            $("#user-icon-chevron").removeClass("fa-chevron-down");
            $("#user-icon-chevron").addClass("fa-chevron-up");
            $("#user-dropdown").show();
        }
        else {
            $("#user-icon-chevron").removeClass("fa-chevron-up");
            $("#user-icon-chevron").addClass("fa-chevron-down");
            $("#user-dropdown").hide();
        }
    });
});