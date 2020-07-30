new Vue({
    el: '#img-form',
    delimiters: ['[[', ']]'],
    data: {
        fileData: ''
    },
    methods: {
        handleFile: function () {
            file = event.target.files[0]
            this.fileData = file.name
        }
    }
})