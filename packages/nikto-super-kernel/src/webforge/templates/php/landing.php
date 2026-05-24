<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{{title}}</h1>
            <p class="tagline">{{tagline}}</p>
        </header>
        <main>
            <section class="hero">
                <div class="hero-content">
                    <h2>{{hero_title}}</h2>
                    <p>{{hero_text}}</p>
                </div>
            </section>
            <section class="features">
                {{features}}
            </section>
        </main>
        <footer>
            <p>&copy; {{year}} {{company}}. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
