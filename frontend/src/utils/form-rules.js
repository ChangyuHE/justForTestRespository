/**
 * Common Vuetify form rules
 */
export default {
    required(value) {
        return !!value || 'Required'
    },
    lengthRange(value, min, max) {
        if (!value || value.length < min || value.length > max)
            return `Must be between ${min} and ${max} symbols`
        return true
    },
    isLongEnough(value, limit=5) {
        if (value && value.length > limit) {
            return true
        } else {
            return `At least ${limit} symbols`
        }
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
    },
    uniqueNameInBranch(value, neighbours) {
        return neighbours.includes(value) ? 'Already exists in current branch \u2014 please take another' : true
    }
}
