$(document).ready(function () {
    $('.product_carousel').owlCarousel({
        stagePadding: 10,
        loop: false,
        margin: 10,
        nav: true,
        responsive: {
            0: {
                items: 1
            },
            550: {
                items: 2
            },
            800: {
                items: 3
            },
            1000: {
                items: 4
            },
            1200: {
                items: 5
            },
        }
    });
});