setInterval(() => {
    window.location.reload()
}, 3 * 60 * 1000)

const navigate = (x) => {
    return '/'+x
    // return window.location.href.substring(0, window.location.href.lastIndexOf('/')) + '/' + x + window.location.href.substring(window.location.href.lastIndexOf('-'))
}
const show_hide_btns = () => {
    var buttons = document.querySelector('.buttons')
    if (buttons.style.getPropertyValue('display') === 'flex') {
        buttons.style.setProperty('display', 'none')
    } else {
        buttons.style.setProperty('display', 'flex')
    }
}