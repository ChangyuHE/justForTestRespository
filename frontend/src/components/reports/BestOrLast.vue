<template>
    <v-card class="my-4 elevation-3">
        <v-card-title class="mb-n6 ml-4">
            <span v-if="type == 'best'">
                Best result for validations:
            </span>
            <span v-else-if="type == 'last'">
                Last result for validations:
            </span>
            <v-spacer></v-spacer>
            <!-- Search field -->
            <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="Search"
                hide-details
                class="pt-0 mt-0"
            ></v-text-field>

            <v-btn light small fab class="ml-4 elevation-5" @click="reportExcel">
                <v-icon>$excel</v-icon>
            </v-btn>
        </v-card-title>

        <!-- Validations list -->
        <v-col class="d-flex">
            <v-list dense flat class="ml-4">
                <v-list-item v-for="(item, i) in branches" :key="i">
                    <v-list-item-content class="py-0 my-1">
                        <v-list-item-title v-text="item"></v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>

            <v-spacer></v-spacer>

            <!-- Grouping type buttons -->
            <label class="d-flex align-start mt-4 mr-1 subtitle-1">
                Group by:
                <v-btn-toggle
                    v-model="reportGrouping"
                    class="d-flex justify-end ml-2" color="teal" mandatory
                    @change="changeGrouping"
                >
                    <v-btn small v-for="name in reportGroups" :key="name">
                        {{ name }}
                    </v-btn>
                </v-btn-toggle>
            </label>
        </v-col>

        <v-divider class="horizontal-line"></v-divider>

        <!-- DataTable -->
        <v-data-table class="results-table"
            :headers="headers"
            :items="items"
            :search="search"
            :loading="reportLoading || excelLoading"
            disable-pagination hide-default-footer multi-sort
        >
            <template v-slot:item.passrate="{ item }">
                <v-chip :color="getPassrateColor(item.passrate)" label>{{ item.passrate }}</v-chip>
            </template>
        </v-data-table>
    </v-card>
</template>

<script>
    import { mapState, mapGetters } from 'vuex'

    export default {
        data() {
            return {
                search: '',
                reportGrouping: 0,
                reportGroups: ['feature', 'component'],
            }
        },
        props: {
            type: { type: String, required: true }
        },
        computed: {
            ...mapState('tree', ['validations']),
            ...mapGetters('tree', ['branches']),
            ...mapState('reports', ['showReport', 'reportLoading', 'excelLoading']),
            ...mapState('reports', {'headers': 'originalHeaders', 'items':'originalItems'}),
            url() {
                return `api/report/${this.type}/${this.validations}`
            }
        },
        methods: {
            reportExcel() {
                const url = `${this.url}?report=excel&group-by=${this.reportGroups[this.reportGrouping]}`
                this.$store
                    .dispatch('reports/reportExcel', { url })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" excel report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    });
            },
            changeGrouping() {
                this.reportWeb();
            },
            reportWeb() {
                const url = `${this.url}?group-by=${this.reportGroups[this.reportGrouping]}`
                this.$store
                    .dispatch('reports/reportWeb', { url })
                    .catch(error => {
                        if (error.handleGlobally) {
                            error.handleGlobally(`Failed in "${this.type}" web report`, url)
                        } else {
                            this.$toasted.global.alert_error(error)
                        }
                    });
            },
            /**
             * Coloring passrates in report
             */
            getPassrateColor(p) {
                p = Number(p.slice(0, -1));
                if (Number.isNaN(p))
                    p = 0;
                if (p >= 0 && p < 50) return 'red lighten-3'
                else if (p >= 50 && p < 80) return 'yellow lighten-4'
                else if (p >= 80 && p < 100) return 'green lighten-4'
                else return 'green lighten-1'
            },
        },
        mounted() {
            this.reportWeb();
        }
    }
</script>

<style>

</style>