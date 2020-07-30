var articleGood = {
    delimiters: ['[[ ', ']]'],
    data: function () {
        return {
            gooded: false,
            good_count: 0,
            article_id: '',
            auth: false,
        }
    },
    mounted: function () {
        var elm = this.$el;
        var count = elm.getAttribute('data-count');
        var id = elm.getAttribute('data-id');
        this.good_count = Number(count);
        this.article_id = id;
        var auth = elm.getAttribute('data-authenticated');
        if (auth == 'False') {
            this.auth = false
        } else {
            this.auth = true
        }
    },
    template: '<div class="mb-auto"><button @click="changeGood" class="border border-0 bg-white"><i :class="heart"></i></button><span>[[ good_count ]]</span></div>',
    computed: {
        heart: function () {
            return {
                fas: this.gooded,
                far: !this.gooded,
                'fa-heart': true,
                'fa-blue': true
            }
        }
    },
    methods: {
        changeGood: function () {
            if (this.auth) {
                const queries = { pk: this.article_id }
                axios.get('/snsapp/change_good/', { params: queries });
                if (this.gooded) {
                    this.good_count -= 1;
                } else {
                    this.good_count += 1;
                }
                this.gooded = !this.gooded;
            } else {
                return confirm('お気に入り機能はログイン後に使用可能です');
            }
        },
        isGood: function () {
            this.gooded = true;
        }
    }
}

new Vue({
    el: '#article',
    delimiters: ['[[ ', ']]'],
    components: {
        'article-good': articleGood,
    },
    mounted: function () {
        axios.get('/snsapp/gooded_articles/')
            .then(function (response) {
                var article_ids = response.data.article_ids;
                for (var i = 0; i < article_ids.length; i++) {
                    id = String(article_ids[i]);
                    if (this.$refs[id]) {
                        this.$refs[id].isGood();
                    }
                };
            }.bind(this))
            .catch(function (error) {
                console.log(error);
            }.bind(this));
    },
});
