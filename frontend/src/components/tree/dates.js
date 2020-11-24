let today = new Date()
let thisMonth = today.getMonth()
let thisYear = today.getFullYear()

const sliderButtons = [
    {'months': 0, 'text': '1 m'},
    {'months': 2, 'text': '3 m'},
    {'months': 5, 'text': '6 m'},
    {'months': 11, 'text': '1 y'},
]

let monthData = []
let monthLabels = []
let lastDaysData = []
const maxMonthsShown = 12
const daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function leapYear(year) {
    return ((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0)
}

for (let i = (maxMonthsShown - 1); i >= 0; i--) {
    monthLabels[i] = months[thisMonth]
    monthData[i] = thisYear + '-' + (thisMonth + 1)

    if (thisMonth == 1 && leapYear(thisYear)) {
        lastDaysData[i] = 29
    } else {
        lastDaysData[i] = daysInMonths[thisMonth]
    }

    if (thisMonth == 0) {
        thisMonth = 11
        thisYear--
    } else {
        thisMonth--
    }
}

// compose date range start date, like 2020-12-1
function dateStart(i) {
    return monthData[i] + '-1'
}
// compose date range end date, like 2020-12-31
function dateEnd(i) {
    return monthData[i] + '-' + lastDaysData[i]
}

export { monthLabels, lastDaysData, maxMonthsShown, sliderButtons, dateStart, dateEnd }
