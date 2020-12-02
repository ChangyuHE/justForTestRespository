<template>
    <v-dialog
        v-model="show"
        :max-width="options.width"
        :style="{ zIndex: options.zIndex }"
        @keydown.esc="cancel"
    >
        <v-card>
            <v-card-title class="">{{ title }}</v-card-title>
            <v-card-text class="py-2 text-h6">
                {{ message }}
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn @click.native="no" color="blue-grey darken-1" text>No</v-btn>
                <v-btn @click.native="yes" :color="options.color" text>Yes</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
    export default {
        data() {
            return {
                dialog: false,
                resolve: null,
                reject: null,
                message: null,
                title: null,
                options: {
                    width: '40%',
                    zIndex: 200,
                    color: 'primary'
                }
            }
        },
        computed: {
            show: {
                get() {
                    return this.dialog
                },
                set(value) {
                    this.dialog = value
                    if (value === false) {
                        this.no()
                    }
                }
            }
        },
        methods: {
            open(title, message, options) {
                this.dialog = true
                this.title = title
                this.message = message
                this.options = Object.assign(this.options, options)

                return new Promise((resolve, reject) => {
                    this.resolve = resolve
                    this.reject = reject
                })
            },
            yes() {
                this.resolve(true)
                this.dialog = false
            },
            no() {
                this.resolve(false)
                this.dialog = false
            }
        }
    }
</script>
