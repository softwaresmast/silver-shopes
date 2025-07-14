const properties = {
    upgrades: {},
    webapp_url: 'https://ggteam-befk3c79d-ggteams-projects-11d759e0.vercel.app/start',
    default_icon: 'static/image/bitco.png'
};

// Генерация 500 улучшений
for (let i = 1; i <= 500; i++) {
    properties.upgrades[`level_${i}_price`] = i * 100;
}