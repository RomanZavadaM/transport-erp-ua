import Link from "next/link";

const operationalModules = [
  { title: "Автобуси", description: "Парк, стан автобусів, документи й пробіг.", href: "/vehicles/", ready: true },
  { title: "Водії", description: "Картки водіїв, документи, допуски та статус.", href: "/drivers/", ready: true },
  { title: "Маршрути", description: "Маршрути та впорядковані списки зупинок.", href: "/routes/", ready: true },
  { title: "Наряди і рейси", description: "Розклад, рейси на дату та призначення автобуса і водія.", href: "/operations/", ready: true },
  { title: "Випуск на лінію", description: "Медичний, технічний контроль і дозвіл диспетчера.", href: "/release/", ready: true },
  { title: "Шляхові листи", description: "Створення з випущеного наряду, перегляд і друк.", href: "/waybills/", ready: true },
];

const accountingModules = [
  { title: "Технічна служба", description: "СТОІР, планове ТО, технічні огляди, дефекти й ремонти.", href: "/technical/", ready: true },
  { title: "Паливо", description: "Заправки, витрата й контроль пального.", href: "", ready: false },
  { title: "Документи", description: "Строки дії документів і попередження.", href: "", ready: false },
  { title: "Звіти", description: "Робочі та управлінські звіти підприємства.", href: "", ready: false },
];

export default function HomePage() {
  return (
    <main className="app-page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Локальний застосунок</p>
          <h1>TransportERP-UA</h1>
          <p className="subtitle">Оперативна робота транспортного підприємства</p>
        </div>
        <div className="page-toolbar-actions">
          <Link className="button secondary" href="/settings/">
            Підприємство
          </Link>
          <Link className="button secondary" href="/system/">
            Стан системи
          </Link>
        </div>
      </header>

      <section className="section-block">
        <div className="section-heading">
          <h2>Оперативна робота</h2>
          <span>Щоденні задачі диспетчера та служби експлуатації</span>
        </div>
        <div className="module-grid">
          {operationalModules.map((module) =>
            module.ready ? (
              <Link className="module-card" href={module.href} key={module.title}>
                <span className="status-pill ready">Доступно</span>
                <h3>{module.title}</h3>
                <p>{module.description}</p>
              </Link>
            ) : (
              <div className="module-card disabled" key={module.title}>
                <span className="status-pill">Наступний етап</span>
                <h3>{module.title}</h3>
                <p>{module.description}</p>
              </div>
            ),
          )}
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <h2>Облік і контроль</h2>
          <span>Технічна служба, документи та звітність</span>
        </div>
        <div className="module-grid compact">
          {accountingModules.map((module) =>
            module.ready ? (
              <Link className="module-card" href={module.href} key={module.title}>
                <span className="status-pill ready">Доступно</span>
                <h3>{module.title}</h3>
                <p>{module.description}</p>
              </Link>
            ) : (
              <div className="module-card disabled" key={module.title}>
                <span className="status-pill">Заплановано</span>
                <h3>{module.title}</h3>
                <p>{module.description}</p>
              </div>
            ),
          )}
        </div>
      </section>
    </main>
  );
}
