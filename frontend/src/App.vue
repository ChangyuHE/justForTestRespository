/*<template>
  <div id="app">
    <div id="nav">
      <router-link to="/">Home</router-link> |
      <router-link to="/about">About</router-link>
    </div>
    <router-view/>
  </div>
</template>*/
<template>
    <div>
        <div class="container">
            <div class="row">
                <v-jstree
                    :data="data" show-checkbox allow-batch multiple @item-click="itemClick">
                </v-jstree>
            </div>
        </div>
    </div>
</template>

<script>
    import VJstree from 'vue-jstree';
    import server from './server.js';

	export default {
        components: {
            VJstree
        },
        data() {
            return {
                //data: treeData,
                data: null,
                loading: true,
                errored: false
            }
        },
		computed: {

        },
        methods: {
            itemClick(node) {
                //console.log(node.model.text + ' clicked !');
                console.log('node:', node);
            }
        },
        beforeCreate() {
            server
                .get('api/validations/')
                .then(response => {
                    console.log(response.data);
                    this.data = response.data;
                })
                .catch(error => {
                    console.log(error)
                    this.errored = true
                  })
                .finally(() => this.loading = false)
        }
	}
</script>

<style>
    .i-windows {
        background: url(./assets/icons/windows.svg) !important;
    }
    .i-linux {
        background: url(./assets/icons/linux.svg) !important;
    }
    .i-platform {
        background: url(./assets/icons/chip.svg) !important;
    }
    .i-gen {
        background: url(./assets/icons/cpu.svg) !important;
    }
    .i-validation {
        background: url(./assets/icons/list.svg) !important;
    }
    .i-simulation {
        background: url(./assets/icons/simulation.svg) !important;
    }
    .icon-custom {
        width: 20px !important;
        height: 20px !important;
        margin: 2px !important;
        padding: 2px !important;
    }
</style>
