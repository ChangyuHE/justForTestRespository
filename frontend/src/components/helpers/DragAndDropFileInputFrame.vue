<template>
    <div
        @drop.prevent="fileDrop"
        @dragover.prevent="dragIn"
        @dragleave.prevent="dragOut"
        :class="fieldClass" class="pa-2 pt-0 mt-1"
    >
        <slot></slot>
    </div>
</template>

<script>
export default {
    data() {
        return {
            fieldClass: 'drag-out',
            file: null,
        }
    },
    methods: {
        dragIn() {
            this.fieldClass = 'drag-in'
        },
        dragOut(){
            this.fieldClass = 'drag-out'
        },
        fileDrop(e) {
            this.file = e.dataTransfer.files[0]
            this.fieldClass = 'drag-out'
            this.$emit('file-drop', this.file)
        }
    }
}
</script>

<style scoped>
    .drag-in {
        background-color: #CFD8DC;
        border: 2px dashed #78909C;
        border-radius: 12px;
    }
    .drag-out {
        border: 2px dashed #EAEAEA;
        border-radius: 12px;
    }
</style>