Vue.component('star-icon', {
    delimiters: ['[[', ']]'],
    data: function () {
        return {
            right: false,
            star_id: 0,
            eval: 3,
        }
    },
    mounted: function () {
        var elm = this.$el;
        var id = elm.getAttribute('data-id');
        this.star_id = Number(id);
        var evaluation = elm.getAttribute('data-eval');
        this.eval = Number(evaluation);
    },
    template: '<i :class="star"></i>',
    computed: {
        star: function () {
            if (this.star_id <= this.eval) {
                this.right = true;
            } else {
                this.right = false;
            };
            return {
                fas: this.right,
                far: !this.right,
                'fa-star': true,
                'fa-yellow': true,
            };
        }
    },
})

