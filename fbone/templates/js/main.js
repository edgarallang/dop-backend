
$(document).ready(function() {
    $('#left-side').addClass('left-appearing');
    $('#right-side').addClass('right-appearing');

    $("#owl-carousel").owlCarousel({
      items: 1,
      loop: true,
      autoHeight: true,
      autoplay: true
    });
})
