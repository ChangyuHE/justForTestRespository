/**
 * Common Vuetify form rules
 */
export default {
    required(value) {
        return !!value || 'Required'
    },
    isLongEnough(value, limit=5) {
        if (value.length < limit)
            return `At least ${limit} symbols`
        return true
    },
    isValidJson(value, model) {
        if ((model == 'additional_parameters' && value != '') || model == 'simics') {
            try {
                JSON.parse(value)
            } catch (exception) {
                return exception.message
            }
        }
        return true
    }
}
