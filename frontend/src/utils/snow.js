let snowCanvas = ''
let container = null
let snowflakes = []
let width = 0
let height = 0
let angle = 0
let intervalHandle = null
let ctx = null

const INTENSITY = 20
const SPEED = 1.8

const MIN_FLAKE_SCALE = 0.3
const MAX_FLAKE_SCALE = 0.8
const IMAGES_COUNT = 6
const OPACITY = 0.5

let IMAGES = []
let IMAGES_SRC = []

// Initial images loading
for (let i = 1; i <= IMAGES_COUNT; i++) {
    IMAGES_SRC.push(require(`@/assets/images/snow/flake${i}.png`))
}
IMAGES_SRC.forEach(image => {
    let img = new Image()
    img.src = image
    img.onload = () => {
        IMAGES.push(img)
    }
})

export default run => {
    if (IMAGES.length !== IMAGES_COUNT) return
    cleanup()
    if (run) {
        generateCanvas()
        generateSnow()
        drawSnow()
    }
}

function cleanup() {
    if (snowCanvas && snowCanvas.parentNode) {
        snowCanvas.parentNode.removeChild(snowCanvas)
        snowCanvas = null
        ctx = null
    }
    snowflakes = []
    cancelAnimationFrame(intervalHandle)
    height = width = 0
}

function setCanvasSize() {
    function setSize() {
        if (!snowCanvas) return
        let size = window.getComputedStyle(container)
        width = size.width.replace('px', '')
        height = window.innerHeight
        snowCanvas.width = width
        snowCanvas.height = height
    }
    window.onresize = setSize
    setSize()
}

function generateCanvas() {
    // Make the canvas
    let canvas = document.getElementById('fallingSnow')
    if (!canvas) {
        canvas = document.createElement('canvas')
    }
    canvas.id = 'fallingSnow'
    canvas.style.position = 'absolute'
    canvas.style.top = 0
    canvas.style.left = 0
    canvas.style['pointer-events'] = 'none'
    snowCanvas = canvas

    // And append it to the element we should make snow
    container = document.querySelector('html')
    if (!container) {
        console.log('FallingSnow: Could not get element! Aborting.')
        return
    }
    container.appendChild(canvas)
    setCanvasSize() // Resize canvas with window
}

function generateSnow() {
    // Generate the snowflakes
    let numParticles = 10 * INTENSITY
    for (let i = 0; i < numParticles; i++) {
        snowflakes.push({
            x: Math.random() * width,
            y: Math.random() * height,
            d: Math.random() * numParticles,     // density
            a: Math.random() / 100,              // angle
            imgId: Math.floor(Math.random() * IMAGES_COUNT),
            scaleFactor: MIN_FLAKE_SCALE + Math.random() * (MAX_FLAKE_SCALE - MIN_FLAKE_SCALE)
        })
    }
}
function drawSnow() {
    if (!ctx) {
        ctx = snowCanvas.getContext('2d')
        ctx.globalAlpha = OPACITY
    }
    ctx.clearRect(0, 0, width, height)
    for (let i = 0; i < snowflakes.length; i++) {
        let s = snowflakes[i]
        ctx.drawImage(IMAGES[s.imgId], s.x, s.y, 20 * s.scaleFactor, 20 * s.scaleFactor)
    }

    let angleDelta = 0.01 + Math.random() * (0.02 - 0.01)       // random from 0.01 to 0.02
    let sign = Math.round(Math.random()) * 2 - 1                // +/-
    angle += sign * angleDelta

    for (let i = 0; i < snowflakes.length; i++) {
        let s = snowflakes[i]
        // Updating X and Y coordinates
        // We will add 1 to the cos function to prevent negative values which will lead flakes to move upwards
        // Every particle has its own density which can be used to make the downward movement different for each flake
        s.y += Math.abs(Math.cos(angle + s.d + 1) + SPEED / 2) + 0.7
        s.x += (Math.sin(angle) + Math.sin(s.a)) / 2 * SPEED

        // Sending flakes back from the top when it leaves
        // Lets make it a bit more organic and let flakes enter from the left and right also.
        if (s.x > width + 5 || s.x < -5 || s.y > height) {
            if (i % 10 > 0) {
                snowflakes[i] = {
                    x: Math.random() * width,
                    y: -10,
                    d: s.d,
                    a: s.a,
                    imgId: snowflakes[i].imgId,
                    scaleFactor: s.scaleFactor
                }
            } else {
                if (Math.sin(angle) > 0) {
                    // Enter from the left
                    snowflakes[i] = {
                        x: 0,
                        y: Math.random() * height,
                        d: s.d,
                        a: s.a,
                        imgId: snowflakes[i].imgId,
                        scaleFactor: s.scaleFactor
                    }
                } else {
                    // Enter from the right
                    snowflakes[i] = {
                        x: width - 15,
                        y: Math.random() * height,
                        d: s.d,
                        a: s.a,
                        imgId: snowflakes[i].imgId,
                        scaleFactor: s.scaleFactor
                    }
                }
            }
        }
    }
    intervalHandle = requestAnimationFrame(drawSnow, 33)
}
