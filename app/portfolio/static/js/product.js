var productGood = {
    delimiters: ['[[ ', ']]'],
    data: function () {
        return {
            isnew: false,
            gooded: false,
            product_id: '',
            auth: false,
        }
    },
    mounted: function () {
        var elm = this.$el;
        var id = elm.getAttribute('data-id');
        this.product_id = id;
        var auth = elm.getAttribute('data-authenticated');
        if (auth == 'False') {
            this.auth = false
        } else {
            this.auth = true
        }
    },
    template: '<div><span v-if="isnew" class="badge badge-danger">New</span><button @click="changeGood" class="float-right border border-0 bg-white"><i :class="heart"></i></button></div>',
    computed: {
        heart: function () {
            return {
                fas: this.gooded,
                far: !this.gooded,
                'fa-heart': true,
                'fa-red': true
            }
        }
    },
    methods: {
        changeGood: function () {
            if (this.auth) {
                const queries = { pk: this.product_id }
                axios.get('/ecapp/toggle_fav/', { params: queries });
                this.gooded = !this.gooded;
            } else {
                return confirm('お気に入り機能はログイン後に使用可能です');
            }
        },
        isGood: function () {
            this.gooded = true;
        },
        isNew: function () {
            this.isnew = true;
        }
    }
}


new Vue({
    el: '#product',
    delimiters: ['[[ ', ']]'],
    components: {
        'product-good': productGood,
    },
    mounted: function () {
        axios.get('/ecapp/wheather_fav_new/')
            .then(function (response) {
                var fav_ids = response.data.fav_ids;
                for (var i = 0; i < fav_ids.length; i++) {
                    id = String(fav_ids[i]);
                    if (this.$refs[id]) {
                        this.$refs[id].isGood();
                    }
                };
                var new_ids = response.data.new_ids;
                for (var i = 0; i < new_ids.length; i++) {
                    id = String(new_ids[i]);
                    if (this.$refs[id]) {
                        this.$refs[id].isNew();
                    }
                };
            }.bind(this))
            .catch(function (error) {
                console.log(error);
            }.bind(this));
    },
});
