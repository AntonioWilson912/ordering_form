$(document).ready(function () {
  console.log("Bar script loaded.");

  let sidebarCollapsed = false;

  // Sidebar toggle
  $("#toggle-sidebar-btn").click(function (e) {
    e.preventDefault();

    if (sidebarCollapsed) {
      $("#sidebar").removeClass("collapsed");
      $("#toggle-sidebar").css("transform", "rotate(270deg)");
    } else {
      $("#sidebar").addClass("collapsed");
      $("#toggle-sidebar").css("transform", "rotate(90deg)");
    }

    sidebarCollapsed = !sidebarCollapsed;
  });

  // User dropdown toggle
  $("#user-icon").click(function (e) {
    e.stopPropagation();
    $("#user-dropdown").toggleClass("show");
    $("#user-icon-chevron").toggleClass("rotated");
  });

  // Close dropdown when clicking outside
  $(document).click(function () {
    $("#user-dropdown").removeClass("show");
    $("#user-icon-chevron").removeClass("rotated");
  });

  // Close banner - use event delegation for dynamically added banners
  $(document).on("click", ".banner-close", function () {
    $(this)
      .closest(".banner")
      .fadeOut(300, function () {
        $(this).remove();
      });
  });

  // Auto-hide success banners after 5 seconds
  setTimeout(function () {
    $(".banner-success").fadeOut(300, function () {
      $(this).remove();
    });
  }, 5000);
});

// Global function to show banner from JS
function showBanner(message, type) {
  // Remove any existing JS banner
  $("#js-banner").hide();

  // Create new banner
  const banner = $(`
    <div class="banner banner-${type}" style="margin: 15px 20px 0;">
      <span class="banner-text">${message}</span>
      <i class="banner-close fa-solid fa-xmark"></i>
    </div>
  `);

  // Add to container or after navbar
  if ($("#banner-container").length) {
    $("#banner-container").prepend(banner);
  } else {
    $(".navbar").after(banner);
  }

  // Scroll to banner
  $("html, body").animate(
    {
      scrollTop: banner.offset().top - 100,
    },
    300
  );

  // Auto-hide success after 5 seconds
  if (type === "success") {
    setTimeout(function () {
      banner.fadeOut(300, function () {
        $(this).remove();
      });
    }, 5000);
  }

  return banner;
}
