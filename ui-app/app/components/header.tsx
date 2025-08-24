import React from 'react';

// Стили можно вынести в CSS-модули, но для простоты оставим их здесь
const headerStyle: React.CSSProperties = {
    padding: '1rem',
    backgroundColor: '#1a1a1a',
    color: 'white',
    borderBottom: '1px solid #333',
};

const Header = () => {
    return (
        <header style={headerStyle}>
            <h1>Статус-бар / Шапка Приложения</h1>
        </header>
    );
};

export default Header;
