$(document).ready(function () {
  console.log("Bar script loaded.");

  let sidebarCollapsed = false;

  $("#toggle-sidebar-btn").click(function (e) {
    e.preventDefault();

    if (sidebarCollapsed) {
      $("#sidebar").removeClass("collapsed");
      // Pointing left when expanded
      $("#toggle-sidebar").css("transform", "rotate(270deg)");
    } else {
      $("#sidebar").addClass("collapsed");
      // Pointing right when collapsed
      $("#toggle-sidebar").css("transform", "rotate(90deg)");
    }

    sidebarCollapsed = !sidebarCollapsed;
  });

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

  $("#bannerClose").click(function () {
    $("#banner").fadeOut(300);
  });
});
