import React from 'react';
import Link from 'next/link';

const sidebarStyle: React.CSSProperties = {
    width: '250px',
    backgroundColor: '#242424',
    padding: '1rem',
    height: '100vh', // Занимает всю высоту
};

const navLinkStyle: React.CSSProperties = {
    display: 'block',
    color: 'white',
    textDecoration: 'none',
    padding: '10px 15px',
    borderRadius: '5px',
    marginBottom: '10px',
};

const Sidebar = () => {
    return (
        <aside style={sidebarStyle}>
            <nav>
                {/* Ссылки на наши страницы-вкладки */}
                <Link href="/tab1" style={navLinkStyle}>Вкладка 1</Link>
                <Link href="/tab2" style={navLinkStyle}>Вкладка 2</Link>
                <Link href="/tab3" style={navLinkStyle}>Вкладка 3</Link>
            </nav>
        </aside>
    );
};

export default Sidebar;
