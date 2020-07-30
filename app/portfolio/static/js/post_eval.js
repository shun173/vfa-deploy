var starIcon = {
    props: ["eval"],
    delimiters: ['[[', ']]'],
    data: function () {
        return {
            right: false,
            star_id: 0,
        }
    },
    mounted: function () {
        var elm = this.$el;
        var id = elm.getAttribute('data-id');
        this.star_id = Number(id);
    },
    template: '<div @click="changeEval" class="d-inline-block"><i :class="star"></i></div>',
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
                'fa-2x': true
            };
        }
    },
    methods: {
        changeEval: function () {
            this.$emit("change-eval", this.star_id);
        }
    }
}

new Vue({
    el: '#stars',
    delimiters: ['[[', ']]'],
    components: {
        'star-icon': starIcon,
    },
    data: {
        eval: 3,
    },
})