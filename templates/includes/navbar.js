// Closes the sidebar menu
$("#menu-close").click(function(e) {
    e.preventDefault();
    $("#sidebar-wrapper").toggleClass("active");
});

// Opens the sidebar menu
$("#menu-toggle").click(function(e) {
    e.preventDefault();
    var open = true;
    $("#sidebar-wrapper").toggleClass("active");
});

// $(window).click(function() {
//     //Hide the menus if visible
//     if ($("##sidebar-wrapper").is(":visible")) {
//       $("#sidebar-wrapper").toggleClass("active");
//     }
// });
//
// $('#sidebar-wrapper').click(function(event){
//     event.stopPropagation();
// });
