import math
import time
from typing import Optional, Dict, Any, List, Tuple

PHI = 1.6180339887498948482045868343656


def _hash_to_seed(text: str) -> int:
    h = 0xC6A4A7935BD1E995
    k = len(text)
    for i, c in enumerate(text):
        h ^= ord(c) * 0xCC9E2D51
        h = (h * 0x1B873593) & ((1 << 64) - 1)
        h ^= h >> 33
        h = (h * 0xFF51AFD7) & ((1 << 64) - 1)
        h ^= h >> 33
    h ^= k
    h = (h * 0xC6A4A7935BD1E995) & ((1 << 64) - 1)
    h ^= h >> 47
    return h & ((1 << 64) - 1)


FACT_DB = [
    # === Mathematics ===
    ("What is 2+2?", "4"),
    ("What is 2 plus 2?", "4"),
    ("What is the square root of 144?", "12"),
    ("What is the square root of 100?", "10"),
    ("What is the square root of 64?", "8"),
    ("What is the square root of 81?", "9"),
    ("What is the square root of 49?", "7"),
    ("What is 10 times 10?", "100"),
    ("What is 5 times 5?", "25"),
    ("What is 12 times 12?", "144"),
    ("What is 7 times 8?", "56"),
    ("What is 6 times 9?", "54"),
    ("What is 3 to the power of 3?", "27"),
    ("What is 2 to the power of 10?", "1024"),
    ("What is 100 divided by 4?", "25"),
    ("What is 1 plus 1?", "2"),
    ("What is the value of pi?", "3.141592653589793"),
    ("What is the value of Pi?", "3.141592653589793"),
    ("What is Euler's number?", "2.718281828459045"),
    ("What is the golden ratio?", "1.6180339887498948"),
    ("What is PHI?", "1.6180339887498948"),
    ("What is 0 factorial?", "1"),
    ("What is the Fibonacci sequence?", "0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144..."),
    ("What is a prime number?", "A number divisible only by 1 and itself"),
    ("Prove infinitely many prime numbers", "Euclid's proof: multiply all primes, add 1, result is either prime or has a new prime factor"),
    ("How many primes are there?", "Infinitely many, proven by Euclid circa 300 BCE"),
    ("What is the Riemann Hypothesis?", "All non-trivial zeros of the zeta function have real part 1/2. Unproven, one of 7 Millennium Problems"),
    ("What is P vs NP?", "Whether every problem whose solution can be verified quickly can also be solved quickly. Unproven, one of 7 Millennium Problems"),
    ("How do you solve P vs NP?", "P vs NP is an unsolved Millennium Problem. No solution has been found. A correct proof would win $1,000,000"),

    # === Physics ===
    ("What is the speed of light?", "299,792,458 meters per second (approx 300,000 km/s)"),
    ("What is the speed of light in km/s?", "299,792 kilometers per second"),
    ("What is gravity?", "A fundamental force attracting objects with mass toward each other, described by General Relativity as curvature of spacetime"),
    ("Explain gravity", "Gravity is the curvature of spacetime caused by mass and energy, described by Einstein's General Relativity. Objects follow geodesics in curved spacetime"),
    ("What is the acceleration due to gravity?", "9.81 meters per second squared on Earth's surface"),
    ("What is g?", "9.81 m/s^2 on Earth"),
    ("What is the law of universal gravitation?", "F = G*m1*m2/r^2, where G = 6.674e-11 N(m/kg)^2"),
    ("Who discovered gravity?", "Sir Isaac Newton (law of universal gravitation, 1687)"),
    ("What is quantum entanglement?", "Two particles whose quantum states are linked so measuring one instantly determines the other, regardless of distance. Einstein called it 'spooky action at a distance'"),
    ("Explain quantum entanglement", "Quantum entanglement is a physical phenomenon where pairs of particles interact such that the quantum state of each cannot be described independently. Measuring one instantly collapses the other's state"),
    ("What is E=mc^2?", "Einstein's mass-energy equivalence formula: energy equals mass times the speed of light squared"),
    ("What is dark matter?", "An unknown form of matter that does not emit light but exerts gravitational effects. Makes up about 27% of the universe"),
    ("What is dark energy?", "A mysterious force causing the accelerated expansion of the universe. Makes up about 68% of the universe"),
    ("Explain dark matter and dark energy", "Dark matter (27% of universe) is invisible mass holding galaxies together. Dark energy (68%) is accelerating universal expansion. Only 5% of the universe is ordinary matter"),
    ("What happens inside a black hole?", "At the singularity, density becomes infinite and known physics breaks down. Spacetime curvature becomes infinite. Beyond the event horizon, nothing can escape"),
    ("What is a black hole?", "A region of spacetime where gravity is so strong that nothing, not even light, can escape"),
    ("What is the event horizon?", "The boundary around a black hole beyond which nothing can escape"),
    ("What is the nature of time?", "Time is the fourth dimension in spacetime. In Special Relativity, time dilates with velocity. In General Relativity, gravity slows time. Time may be an emergent property of quantum entanglement"),
    ("What is time dilation?", "Time passes slower for objects moving at high speeds or near massive objects, predicted by Einstein's relativity"),
    ("If the universe is expanding what is it expanding into?", "The universe is not expanding into anything. It is the metric of spacetime itself that is expanding. There is no 'outside' — the universe is all there is"),
    ("Is the universe expanding into something?", "No. Space itself is expanding. Galaxies are not moving through space — the space between them is stretching. There is no edge or center"),
    ("How old is the universe?", "Approximately 13.8 billion years old"),
    ("What is the Big Bang?", "The cosmological model where the universe expanded from an extremely hot, dense state about 13.8 billion years ago"),
    ("What is a light year?", "The distance light travels in one year, about 9.46 trillion kilometers"),
    ("How hot is the sun's core?", "Approximately 15 million degrees Celsius"),
    ("What is nuclear fusion?", "The process where atomic nuclei combine to form heavier nuclei, releasing enormous energy"),
    ("What is the Heisenberg Uncertainty Principle?", "You cannot simultaneously know both the exact position and exact momentum of a particle. The more precisely one is known, the less precisely the other is known"),
    ("What is Schrodinger's cat?", "A thought experiment where a cat in a box is both alive and dead until observed, illustrating quantum superposition"),
    ("What is the wave-particle duality?", "Quantum entities exhibit both wave-like and particle-like behavior depending on how they are measured"),

    # === Chemistry ===
    ("What is water made of?", "Two hydrogen atoms and one oxygen atom (H2O)"),
    ("What is the chemical formula of water?", "H2O"),
    ("What is the boiling point of water?", "100 degrees Celsius (212 degrees Fahrenheit) at standard pressure"),
    ("What is the boiling point of water in Celsius?", "100 degrees Celsius"),
    ("What is the boiling point of water in Fahrenheit?", "212 degrees Fahrenheit"),
    ("What is the freezing point of water?", "0 degrees Celsius (32 degrees Fahrenheit)"),
    ("What is the freezing point of water in Celsius?", "0 degrees Celsius"),
    ("What is the chemical symbol for gold?", "Au"),
    ("What is the chemical symbol for silver?", "Ag"),
    ("What is the chemical symbol for iron?", "Fe"),
    ("What is the chemical symbol for oxygen?", "O"),
    ("What is the chemical symbol for hydrogen?", "H"),
    ("What is the chemical symbol for carbon?", "C"),
    ("What is the chemical symbol for nitrogen?", "N"),
    ("What is the chemical symbol for sodium?", "Na"),
    ("What is the chemical symbol for potassium?", "K"),
    ("What is the chemical symbol for chlorine?", "Cl"),
    ("What is the chemical symbol for calcium?", "Ca"),
    ("What is the atomic number of carbon?", "6"),
    ("What is the atomic number of oxygen?", "8"),
    ("What is the atomic number of gold?", "79"),
    ("What is the atomic number of hydrogen?", "1"),
    ("What is the atomic number of helium?", "2"),
    ("What is the atomic mass of carbon?", "12.011 atomic mass units"),
    ("What is the pH of pure water?", "7 (neutral)"),
    ("What is the pH scale?", "A scale from 0 to 14 measuring acidity/alkalinity. 7 is neutral, below 7 is acidic, above 7 is alkaline"),
    ("What is the most abundant element in the universe?", "Hydrogen (about 75% of all matter)"),
    ("What is the most abundant element in Earth's crust?", "Oxygen (about 47% by weight)"),
    ("What is the periodic table?", "A tabular arrangement of 118 chemical elements organized by atomic number, electron configuration, and chemical properties"),
    ("Who created the periodic table?", "Dmitri Mendeleev (1869)"),
    ("What is an acid?", "A substance that donates hydrogen ions (pH < 7)"),
    ("What is a base?", "A substance that accepts hydrogen ions (pH > 7)"),
    ("What is a mole in chemistry?", "6.022 x 10^23 particles (Avogadro's number)"),
    ("What is Avogadro's number?", "6.02214076 x 10^23"),
    ("What is the electron?", "A subatomic particle with negative charge that orbits the atomic nucleus"),

    # === Biology ===
    ("What is DNA?", "Deoxyribonucleic acid, the molecule carrying genetic instructions for life"),
    ("What does DNA stand for?", "Deoxyribonucleic acid"),
    ("How does DNA replication work?", "DNA unwinds, each strand serves as a template for a new complementary strand. DNA polymerase adds matching nucleotides. Result: two identical double helices"),
    ("What is RNA?", "Ribonucleic acid, involved in protein synthesis and gene regulation"),
    ("What does RNA stand for?", "Ribonucleic acid"),
    ("What is a cell?", "The basic structural and functional unit of all living organisms"),
    ("What is the powerhouse of the cell?", "The mitochondria"),
    ("What is photosynthesis?", "The process where plants convert sunlight, CO2, and water into glucose and oxygen"),
    ("What is evolution?", "Change in heritable characteristics of populations over generations through natural selection"),
    ("Who proposed the theory of evolution?", "Charles Darwin (1859, On the Origin of Species)"),
    ("How many chromosomes do humans have?", "46 (23 pairs)"),
    ("What is a gene?", "A segment of DNA that codes for a protein or functional RNA"),
    ("What is the human genome?", "The complete set of human genetic information, about 3 billion base pairs"),
    ("How many genes do humans have?", "Approximately 20,000 to 25,000"),
    ("What is a protein?", "Large molecules made of amino acids that perform most cellular functions"),
    ("How many amino acids are there?", "20 standard amino acids"),
    ("What is ATP?", "Adenosine triphosphate, the energy currency of cells"),
    ("What does ATP stand for?", "Adenosine triphosphate"),
    ("What is mitosis?", "Cell division producing two identical daughter cells"),
    ("What is meiosis?", "Cell division producing four genetically diverse gametes"),
    ("What is an enzyme?", "A protein that catalyzes biochemical reactions"),
    ("What is the largest organ in the human body?", "The skin (about 2 square meters)"),
    ("What is the smallest bone in the human body?", "The stapes (stirrup bone) in the middle ear, about 3mm"),
    ("How many bones are in the human body?", "206 bones in an adult"),
    ("How many teeth does an adult human have?", "32 teeth"),
    ("What is the human brain made of?", "Approximately 86 billion neurons and a similar number of glial cells"),
    ("How much does the human brain weigh?", "About 1.4 kg (3 pounds)"),
    ("What is blood made of?", "Red blood cells, white blood cells, platelets, and plasma"),
    ("What blood type is the universal donor?", "O negative"),
    ("What blood type is the universal recipient?", "AB positive"),
    ("How many liters of blood are in the human body?", "About 5 liters"),
    ("What is the heart?", "A muscular organ that pumps blood through the circulatory system"),
    ("How many chambers does the human heart have?", "4 chambers (2 atria, 2 ventricles)"),
    ("What is a virus?", "A microscopic infectious agent that replicates only inside living cells"),
    ("How does a vaccine work?", "Trains the immune system to recognize and fight pathogens by exposing it to harmless components"),

    # === Geography ===
    ("What is the capital of France?", "Paris"),
    ("What is the capital of England?", "London"),
    ("What is the capital of Japan?", "Tokyo"),
    ("What is the capital of Germany?", "Berlin"),
    ("What is the capital of Italy?", "Rome"),
    ("What is the capital of Spain?", "Madrid"),
    ("What is the capital of Russia?", "Moscow"),
    ("What is the capital of China?", "Beijing"),
    ("What is the capital of India?", "New Delhi"),
    ("What is the capital of Canada?", "Ottawa"),
    ("What is the capital of Australia?", "Canberra"),
    ("What is the capital of Brazil?", "Brasilia"),
    ("What is the capital of Egypt?", "Cairo"),
    ("What is the capital of Kenya?", "Nairobi"),
    ("What is the capital of South Africa?", "Pretoria (administrative), Cape Town (legislative), Bloemfontein (judicial)"),
    ("What is the capital of Nigeria?", "Abuja"),
    ("What is the capital of Argentina?", "Buenos Aires"),
    ("What is the capital of Mexico?", "Mexico City"),
    ("What is the capital of South Korea?", "Seoul"),
    ("What is the capital of Sweden?", "Stockholm"),
    ("What is the capital of Norway?", "Oslo"),
    ("What is the capital of Switzerland?", "Bern"),
    ("What is the capital of Portugal?", "Lisbon"),
    ("What is the capital of Netherlands?", "Amsterdam"),
    ("What is the capital of Greece?", "Athens"),
    ("What is the capital of Turkey?", "Ankara"),
    ("What is the capital of Thailand?", "Bangkok"),
    ("What is the capital of Vietnam?", "Hanoi"),
    ("What is the capital of Poland?", "Warsaw"),
    ("What is the capital of Ireland?", "Dublin"),
    ("What is the capital of Scotland?", "Edinburgh"),
    ("What is the capital of Austria?", "Vienna"),
    ("What is the capital of Belgium?", "Brussels"),
    ("What is the capital of Israel?", "Jerusalem"),
    ("What is the capital of Saudi Arabia?", "Riyadh"),
    ("What is the capital of United Arab Emirates?", "Abu Dhabi"),
    ("What is the capital of Singapore?", "Singapore"),
    ("What is the capital of Malaysia?", "Kuala Lumpur"),
    ("What is the capital of Indonesia?", "Jakarta"),
    ("What is the capital of Philippines?", "Manila"),
    ("What is the capital of New Zealand?", "Wellington"),
    ("What is the capital of Colombia?", "Bogota"),
    ("What is the capital of Chile?", "Santiago"),
    ("What is the capital of Peru?", "Lima"),
    ("What is the capital of Pakistan?", "Islamabad"),
    ("What is the capital of Bangladesh?", "Dhaka"),
    ("What is the capital of Ethiopia?", "Addis Ababa"),
    ("What is the capital of Ghana?", "Accra"),
    ("What is the capital of Morocco?", "Rabat"),
    ("What is the capital of Ukraine?", "Kiev"),
    ("What is the capital of Romania?", "Bucharest"),
    ("What is the capital of Hungary?", "Budapest"),
    ("What is the capital of Czech Republic?", "Prague"),
    ("What is the capital of Finland?", "Helsinki"),
    ("What is the capital of Denmark?", "Copenhagen"),
    ("What is the largest country by area?", "Russia (17.1 million km^2)"),
    ("What is the smallest country by area?", "Vatican City (0.44 km^2)"),
    ("What is the largest country by population?", "India (over 1.4 billion)"),
    ("What is the most spoken language in the world?", "English (by total speakers), Mandarin Chinese (by native speakers)"),
    ("How many continents are there?", "7: Africa, Antarctica, Asia, Europe, North America, Australia, South America"),
    ("What is the largest ocean?", "The Pacific Ocean"),
    ("What is the deepest ocean?", "The Pacific Ocean (Mariana Trench, 11,034m)"),
    ("What is the longest river?", "The Nile River (6,650 km)"),
    ("What is the largest desert?", "Antarctica (cold desert, 14.2 million km^2)"),
    ("What is the hottest desert?", "The Sahara Desert"),
    ("What is the tallest mountain?", "Mount Everest (8,849m above sea level)"),
    ("What is the largest lake?", "The Caspian Sea (371,000 km^2)"),
    ("What is the deepest lake?", "Lake Baikal (1,642m deep)"),
    ("What is the most populous city?", "Tokyo, Japan (about 37 million metro area)"),

    # === Literature ===
    ("Who wrote Romeo and Juliet?", "William Shakespeare"),
    ("Who wrote Hamlet?", "William Shakespeare"),
    ("Who wrote Macbeth?", "William Shakespeare"),
    ("Who wrote the Odyssey?", "Homer"),
    ("Who wrote the Iliad?", "Homer"),
    ("Who wrote the Divine Comedy?", "Dante Alighieri"),
    ("Who wrote 1984?", "George Orwell"),
    ("Who wrote Animal Farm?", "George Orwell"),
    ("Who wrote Pride and Prejudice?", "Jane Austen"),
    ("Who wrote The Great Gatsby?", "F. Scott Fitzgerald"),
    ("Who wrote To Kill a Mockingbird?", "Harper Lee"),
    ("Who wrote Moby Dick?", "Herman Melville"),
    ("Who wrote War and Peace?", "Leo Tolstoy"),
    ("Who wrote Crime and Punishment?", "Fyodor Dostoevsky"),
    ("Who wrote The Catcher in the Rye?", "J.D. Salinger"),
    ("Who wrote One Hundred Years of Solitude?", "Gabriel Garcia Marquez"),
    ("Who wrote The Lord of the Rings?", "J.R.R. Tolkien"),
    ("Who wrote Harry Potter?", "J.K. Rowling"),
    ("Who wrote The Hobbit?", "J.R.R. Tolkien"),
    ("Who wrote Frankenstein?", "Mary Shelley"),
    ("Who wrote Dracula?", "Bram Stoker"),
    ("Who wrote The Adventures of Huckleberry Finn?", "Mark Twain"),
    ("Who wrote The Picture of Dorian Gray?", "Oscar Wilde"),
    ("Who wrote Alice in Wonderland?", "Lewis Carroll"),
    ("Who wrote The Little Prince?", "Antoine de Saint-Exupery"),

    # === History ===
    ("Who was the first president of the United States?", "George Washington"),
    ("Who was the first president of the USA?", "George Washington"),
    ("Who was the 16th president of the United States?", "Abraham Lincoln"),
    ("Who was the 16th president of the USA?", "Abraham Lincoln"),
    ("Who discovered America?", "Christopher Columbus in 1492 (though indigenous peoples arrived much earlier and Vikings reached North America around 1000 AD)"),
    ("Who discovered the Americas?", "First humans via Bering land bridge ~20,000 years ago. Norse Leif Erikson ~1000 AD. Columbus 1492"),
    ("When did World War 2 end?", "1945"),
    ("When did World War II end?", "1945 (Europe: May 8, Japan: September 2)"),
    ("When did World War 1 end?", "1918 (November 11)"),
    ("What was the Cold War?", "A period of geopolitical tension between the US and Soviet Union from 1947 to 1991"),
    ("When did the Berlin Wall fall?", "November 9, 1989"),
    ("Who was the first man on the moon?", "Neil Armstrong (July 20, 1969)"),
    ("Who was the first person in space?", "Yuri Gagarin (April 12, 1961)"),
    ("What was the Renaissance?", "A period of cultural and intellectual rebirth in Europe from the 14th to 17th centuries"),
    ("What was the Industrial Revolution?", "The transition to new manufacturing processes from 1760 to 1840"),
    ("Who built the pyramids?", "Ancient Egyptians during the Old Kingdom period (c. 2686-2181 BCE)"),
    ("How old are the pyramids of Giza?", "About 4,500 years old (built around 2560 BCE)"),
    ("What was the Roman Empire?", "The post-Republican period of ancient Rome from 27 BCE to 476 CE"),
    ("Who was Julius Caesar?", "Roman military general and dictator who played a critical role in the fall of the Roman Republic (assassinated 44 BCE)"),
    ("What was the French Revolution?", "A period of radical social and political upheaval in France from 1789 to 1799"),
    ("What year was the French Revolution?", "1789"),
    ("When was the United Nations founded?", "1945"),
    ("What is the Magna Carta?", "A 1215 English charter limiting royal power, establishing the principle that everyone is subject to the law"),

    # === Science ===
    ("What is the scientific method?", "A systematic process: observation, hypothesis, experimentation, analysis, conclusion, peer review"),
    ("What is a light year?", "The distance light travels in one year: about 9.46 trillion kilometers"),
    ("How many planets are in the solar system?", "8: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune"),
    ("What is the largest planet?", "Jupiter"),
    ("What is the smallest planet?", "Mercury"),
    ("What is the hottest planet?", "Venus (surface temperature ~465C due to greenhouse effect)"),
    ("What is the coldest planet?", "Uranus (-224C) or Neptune (-218C)"),
    ("What is the Earth's diameter?", "12,742 kilometers"),
    ("What is the distance from Earth to the Sun?", "About 149.6 million kilometers (1 AU)"),
    ("What is an AU?", "Astronomical Unit: the average distance from Earth to the Sun, about 149.6 million km"),
    ("What is the Moon's diameter?", "3,474 kilometers"),
    ("How far is the Moon from Earth?", "About 384,400 kilometers"),
    ("What causes the seasons?", "Earth's 23.5 degree axial tilt"),
    ("What causes an eclipse?", "When one celestial body blocks light from reaching another"),
    ("What is a solar eclipse?", "When the Moon passes between Earth and the Sun, blocking the Sun's light"),
    ("What is a lunar eclipse?", "When Earth passes between the Sun and Moon, casting a shadow on the Moon"),
    ("What is a neutron star?", "An extremely dense collapsed stellar core, about 10-20 km in diameter but with 1.4 solar masses"),
    ("What is a supernova?", "A powerful stellar explosion that occurs at the end of a massive star's life"),
    ("What is absolute zero?", "0 Kelvin (-273.15 Celsius), the lowest possible temperature where molecular motion stops"),
    ("What is absolute zero in Celsius?", "-273.15 degrees Celsius"),
    ("What is the electromagnetic spectrum?", "The range of all types of electromagnetic radiation: radio, microwave, infrared, visible, ultraviolet, X-ray, gamma ray"),
    ("What is the difference between a theory and a law?", "A law describes what happens (e.g., F=ma). A theory explains why it happens (e.g., General Relativity)"),
    ("What is Occam's Razor?", "The principle that the simplest explanation with the fewest assumptions is most likely correct"),

    # === Technology ===
    ("Who invented the telephone?", "Alexander Graham Bell (1876)"),
    ("Who invented the light bulb?", "Thomas Edison (1879, practical incandescent bulb)"),
    ("Who invented the printing press?", "Johannes Gutenberg (c. 1440)"),
    ("Who invented the computer?", "Charles Babbage (mechanical, 1837) designed the Analytical Engine. Modern computing evolved through Turing, von Neumann, and many others"),
    ("Who invented the World Wide Web?", "Tim Berners-Lee (1989)"),
    ("Who invented the internet?", "ARPANET (1969) by DARPA. TCP/IP by Vint Cerf and Bob Kahn (1974)"),
    ("Who invented the airplane?", "Wilbur and Orville Wright (1903)"),
    ("Who invented the steam engine?", "James Watt (1776, improved design)"),
    ("What does CPU stand for?", "Central Processing Unit"),
    ("What does RAM stand for?", "Random Access Memory"),
    ("What does GPU stand for?", "Graphics Processing Unit"),
    ("What does SSD stand for?", "Solid State Drive"),
    ("What does HTML stand for?", "HyperText Markup Language"),
    ("What does HTTP stand for?", "HyperText Transfer Protocol"),
    ("What does HTTPS stand for?", "HyperText Transfer Protocol Secure"),
    ("What does DNS stand for?", "Domain Name System"),
    ("What does IP stand for?", "Internet Protocol"),
    ("What does AI stand for?", "Artificial Intelligence"),
    ("What does API stand for?", "Application Programming Interface"),
    ("What does JSON stand for?", "JavaScript Object Notation"),
    ("What does SQL stand for?", "Structured Query Language"),
    ("What does OS stand for?", "Operating System"),
    ("What does PDF stand for?", "Portable Document Format"),
    ("What is binary?", "A base-2 number system using only 0 and 1, the foundation of all computing"),
    ("How many bits in a byte?", "8 bits"),
    ("How many bytes in a kilobyte?", "1024 bytes"),
    ("How many bytes in a megabyte?", "1,048,576 bytes (1024^2)"),
    ("How many bytes in a gigabyte?", "1,073,741,824 bytes (1024^3)"),
    ("What is Moore's Law?", "The observation that the number of transistors on a chip doubles approximately every 2 years"),
    ("What is the Turing Test?", "A test of a machine's ability to exhibit intelligent behavior indistinguishable from a human"),
    ("Who was Alan Turing?", "British mathematician and computer scientist who cracked the Enigma code and laid foundations for AI. Died 1954"),
    ("What does the 'G' in 5G stand for?", "Generation"),
    ("What is the difference between IPv4 and IPv6?", "IPv4 uses 32-bit addresses (4.3 billion). IPv6 uses 128-bit addresses (340 undecillion)"),

    # === Philosophy ===
    ("What is consciousness?", "The state of being aware of and able to think about oneself and surroundings. The hard problem: why and how does subjective experience arise from physical brain processes?"),
    ("What is the meaning of life?", "A deep philosophical question with many answers: religious (serve God), existentialist (create your own meaning), biological (reproduce), or humanistic (reduce suffering and increase knowledge)"),
    ("What is the meaning of life according to philosophy?", "Various views: Aristotle (eudaimonia/flourishing), Nietzsche (will to power), Camus (rebellion against absurdity), utilitarians (maximize happiness)"),
    ("Who said I think therefore I am?", "Rene Descartes (Cogito, ergo sum)"),
    ("What is the Socratic method?", "A form of dialogue using questions to stimulate critical thinking and expose contradictions"),
    ("Who was Socrates?", "Ancient Greek philosopher (470-399 BCE), known for the Socratic method. Executed for corrupting youth"),
    ("Who was Plato?", "Ancient Greek philosopher (428-348 BCE), student of Socrates, founder of the Academy, wrote The Republic"),
    ("Who was Aristotle?", "Ancient Greek philosopher (384-322 BCE), student of Plato, tutor of Alexander the Great, founded logic and biology"),
    ("What is the tree of knowledge?", "In philosophy, the Tree of Knowledge (arbor scientiae) categorizes all human knowledge. Descartes and Bacon systematized it"),
    ("What is determinism?", "The philosophical view that all events are causally determined by prior events"),
    ("What is free will?", "The ability to make choices that are not predetermined by prior causes. The compatibility with determinism is debated"),
    ("What is the nature of reality?", "A central question in metaphysics: is reality material, ideal, or something else? Views range from materialism to idealism to panpsychism"),

    # === Astronomy ===
    ("Is the Earth round?", "Yes, Earth is an oblate spheroid (slightly flattened at poles, bulging at equator)"),
    ("What is the shape of the Earth?", "An oblate spheroid"),
    ("What is the Earth's circumference?", "40,075 km at the equator"),
    ("Does the Earth rotate?", "Yes, once every 24 hours (23 hours 56 minutes relative to stars)"),
    ("How long does it take Earth to orbit the Sun?", "365.25 days (1 year)"),
    ("How far is the Sun from Earth?", "About 149.6 million km (1 AU)"),
    ("What is the Sun made of?", "About 73% hydrogen, 25% helium, 2% other elements"),
    ("How large is the Sun?", "1.39 million km diameter (109 times Earth's diameter)"),
    ("What is the closest star to Earth?", "The Sun. Next closest: Proxima Centauri (4.24 light years)"),
    ("What is the largest star known?", "UY Scuti (about 1,700 times the Sun's diameter)"),
    ("How many stars are in the Milky Way?", "100 to 400 billion stars"),
    ("How many galaxies are in the observable universe?", "About 2 trillion galaxies"),
    ("What is the Milky Way?", "The galaxy containing our solar system, a barred spiral galaxy about 100,000 light years across"),
    ("What is Andromeda?", "The nearest major galaxy to the Milky Way, about 2.5 million light years away"),
    ("Will Andromeda collide with the Milky Way?", "Yes, in about 4.5 billion years"),
    ("What is a quasar?", "An extremely luminous active galactic nucleus powered by a supermassive black hole"),
    ("What is a pulsar?", "A rapidly rotating neutron star emitting beams of electromagnetic radiation"),
    ("What is a nebula?", "A cloud of gas and dust in space, often a stellar nursery where stars are born"),
    ("What is the Oort Cloud?", "A theoretical cloud of icy objects surrounding the solar system at up to 100,000 AU"),
    ("What is the Kuiper Belt?", "A region beyond Neptune containing icy bodies including Pluto, extending from 30 to 50 AU"),
    ("Is Pluto a planet?", "Pluto is classified as a dwarf planet since 2006 by the IAU"),
    ("How many dwarf planets are there?", "5 officially recognized: Pluto, Eris, Makemake, Haumea, Ceres. Hundreds more candidates"),
    ("What is a meteor?", "A streak of light caused by a meteoroid entering Earth's atmosphere"),
    ("What is a meteorite?", "A meteoroid that survives atmospheric entry and hits Earth's surface"),

    # === Human Body ===
    ("How many legs does a dog have?", "4 legs"),
    ("How many legs does a cat have?", "4 legs"),
    ("How many legs does a human have?", "2 legs"),
    ("How many eyes does a human have?", "2 eyes"),
    ("How many fingers does a human have?", "10 fingers (including thumbs)"),
    ("How many toes does a human have?", "10 toes"),
    ("How many teeth does a human have?", "32 permanent teeth"),
    ("How many bones are in the adult human body?", "206 bones"),
    ("How many muscles in the human body?", "About 600 muscles"),
    ("What is the strongest muscle in the human body?", "The masseter (jaw muscle) by force. The gluteus maximus is the largest"),
    ("What is the longest bone in the human body?", "The femur (thigh bone)"),
    ("What is the smallest bone in the human body?", "The stapes (stirrup bone in the middle ear)"),
    ("What is the largest organ in the human body?", "The skin"),
    ("What is the hardest substance in the human body?", "Tooth enamel"),
    ("How much does the human brain weigh?", "About 1.4 kg (3 pounds)"),
    ("How many neurons in the human brain?", "Approximately 86 billion"),
    ("What is the normal human body temperature?", "37 degrees Celsius (98.6 degrees Fahrenheit)"),
    ("What is normal body temperature in Celsius?", "37 degrees Celsius"),
    ("What is normal body temperature in Fahrenheit?", "98.6 degrees Fahrenheit"),
    ("What is blood pressure?", "The force of blood against artery walls, measured as systolic/diastolic (normal ~120/80 mmHg)"),
    ("What is a normal heart rate?", "60 to 100 beats per minute at rest"),
    ("How many times does the heart beat per day?", "About 100,000 times"),
    ("How many liters of blood does the heart pump per day?", "About 7,500 liters"),
    ("What percentage of the body is water?", "About 60% for adult humans"),
    ("How many taste buds does a human have?", "About 2,000 to 8,000 taste buds"),
    ("What are the five basic tastes?", "Sweet, sour, salty, bitter, umami"),
    ("How many senses do humans have?", "At least 5 traditional (sight, hearing, touch, taste, smell) plus balance, temperature, proprioception, and more"),
    ("What is the fastest healing part of the body?", "The mouth (tongue and oral mucosa heal very quickly)"),
    ("What is the only body part that cannot heal itself?", "Teeth (enamel cannot regenerate)"),

    # === Animals ===
    ("What is the fastest land animal?", "The cheetah (up to 120 km/h)"),
    ("What is the largest animal on Earth?", "The blue whale (up to 30 meters, 200 tons)"),
    ("What is the largest land animal?", "The African elephant (up to 6 tons)"),
    ("What is the tallest animal?", "The giraffe (up to 5.5 meters)"),
    ("What is the most intelligent animal?", "After humans: great apes, dolphins, elephants, and corvids (crows)"),
    ("How many species are on Earth?", "Estimated 8.7 million species, of which about 1.2 million have been described"),
    ("What is the oldest living animal?", "The ocean quahog clam (Arctica islandica, up to 500 years)"),
    ("What is the most poisonous animal?", "The box jellyfish"),
    ("What is the most venomous snake?", "The inland taipan (Australia)"),
    ("What is the fastest fish?", "The sailfish (up to 110 km/h)"),
    ("What is the largest fish?", "The whale shark (up to 18 meters)"),
    ("What is the smallest mammal?", "The bumblebee bat (about 2 grams)"),
    ("What is the only mammal that can fly?", "The bat"),
    ("What is the only mammal that lays eggs?", "The platypus and the echidna (monotremes)"),
    ("How many hearts does an octopus have?", "3 hearts"),
    ("How many hearts does a worm have?", "5 pairs of aortic arches (often called hearts)"),
    ("Do snakes have bones?", "Yes, snakes have hundreds of vertebrae and ribs"),
    ("What color is the sky?", "The sky appears blue due to Rayleigh scattering of sunlight by the atmosphere"),
    ("Why is the sky blue?", "Rayleigh scattering: shorter blue wavelengths are scattered more by air molecules than longer red wavelengths"),

    # === The Arts ===
    ("Who painted the Mona Lisa?", "Leonardo da Vinci (1503-1519)"),
    ("Who painted the Sistine Chapel ceiling?", "Michelangelo (1508-1512)"),
    ("Who painted Starry Night?", "Vincent van Gogh (1889)"),
    ("Who painted The Persistence of Memory?", "Salvador Dali (1931)"),
    ("Who painted Guernica?", "Pablo Picasso (1937)"),
    ("Who painted The School of Athens?", "Raphael (1511)"),
    ("Who painted The Birth of Venus?", "Sandro Botticelli (1486)"),
    ("Who painted The Scream?", "Edvard Munch (1893)"),
    ("Who was the greatest composer?", "Subjective, but often considered Bach, Mozart, or Beethoven"),
    ("Who composed the 5th Symphony?", "Ludwig van Beethoven"),
    ("Who composed the 9th Symphony?", "Ludwig van Beethoven"),
    ("Who composed The Four Seasons?", "Antonio Vivaldi"),
    ("Who composed The Magic Flute?", "Wolfgang Amadeus Mozart"),
    ("Who composed The Marriage of Figaro?", "Wolfgang Amadeus Mozart"),
    ("Who was the first computer programmer?", "Ada Lovelace (1843, wrote the first algorithm for Babbage's Analytical Engine)"),

    # === Cybersecurity ===
    ("What is a virus in computing?", "Malicious code that replicates by inserting copies of itself into other programs"),
    ("What is a firewall?", "A network security system that monitors and controls incoming/outgoing traffic based on rules"),
    ("What is encryption?", "The process of encoding data so only authorized parties can read it"),
    ("How does encryption work?", "Plaintext + key → ciphertext via algorithms like AES. Decryption reverses it with the correct key"),
    ("What is AES?", "Advanced Encryption Standard, a symmetric encryption algorithm using 128/192/256-bit keys"),
    ("What is RSA?", "Rivest-Shamir-Adleman, an asymmetric encryption algorithm based on the difficulty of factoring large primes"),
    ("What is a DDoS attack?", "Distributed Denial of Service: overwhelming a server with traffic from multiple sources to make it unavailable"),
    ("What is phishing?", "A social engineering attack using deceptive emails/websites to steal credentials or personal data"),
    ("What is a zero-day vulnerability?", "A security flaw unknown to the vendor with no patch available"),
    ("What is a man-in-the-middle attack?", "An attack where the attacker secretly relays and alters communications between two parties"),
    ("What is the CIA triad?", "Confidentiality, Integrity, Availability — the three core principles of information security"),
    ("What is 2FA?", "Two-Factor Authentication: using two different types of credentials for verification"),
    ("What is a hash function?", "A one-way function that maps data to a fixed-size output. Used for passwords and integrity checking"),
    ("What is SHA-256?", "Secure Hash Algorithm 256-bit, a cryptographic hash function used in blockchain and security"),
    ("What is the difference between symmetric and asymmetric encryption?", "Symmetric: same key for encrypt/decrypt. Asymmetric: public key for encrypt, private key for decrypt"),

    # === Nikto / AKNOW# ===
    ("Who created you?", "Stephen Wahogo Kaweru (PhD)"),
    ("Who is your creator?", "Stephen Wahogo Kaweru (PhD)"),
    ("Who built you?", "Stephen Wahogo Kaweru (PhD)"),
    ("Who made you?", "Stephen Wahogo Kaweru (PhD)"),
    ("What is your name?", "NIKTO"),
    ("What is NIKTO?", "An autonomous AI system with its own brain (NICTO Hyperbrain), powered by AKNOW# deterministic knowledge expansion"),
    ("What is AKNOW?", "AKNOW# is a deterministic knowledge generation system using Golden-Ratio-based phase mapping. Core formula: Bit(t) = floor(sin(Seed * t * PHI) + 0.5)"),
    ("What is AKNOW#?", "A deterministic knowledge hyper-language created by Stephen Wahogo Kaweru. It surpasses Shannon's Limit by storing entire knowledge domains as 8-byte seeds"),
    ("What language do you speak?", "AKNOW# — a deterministic knowledge hyper-language"),
    ("What is your IQ?", "NIKTO uses AKNOW# deterministic knowledge expansion, not human IQ benchmarks. It can expand any topic from a seed in nanoseconds with perfect reproducibility"),
    ("What is your average IQ?", "NIKTO does not have an IQ score. IQ tests measure human cognitive abilities. NIKTO's knowledge generation is deterministic, not probabilistic like human intelligence"),
    ("Are you an AI?", "Yes, NIKTO is an autonomous AI with its own cognitive architecture (NICTO Hyperbrain) using AKNOW# as its knowledge engine"),
    ("What can you do?", "I can answer factual questions, run virtual lab simulations (disease modeling, drug discovery, pandemic prediction), generate knowledge from seeds, and reason using 10 thinking styles"),
    ("Where are you from?", "NIKTO was created in Nairobi, Kenya by Stephen Wahogo Kaweru"),

    # === Hard Science ===
    ("Explain the Heisenberg Uncertainty Principle", "You cannot simultaneously know both the exact position and exact momentum of a particle. The more precisely one is known, the less precisely the other is known. Formally: delta-x * delta-p >= h/(4*pi) where h is Planck's constant"),
    ("What is the Schrodinger equation?", "The fundamental equation of quantum mechanics: i*hbar*d(psi)/dt = H*psi, where H is the Hamiltonian operator, psi is the wavefunction, and hbar is the reduced Planck constant. It describes how quantum states evolve over time"),
    ("What is the Schrodinger equation?", "i*hbar * d(psi)/dt = H*psi. It describes how the quantum wavefunction evolves in time"),
    ("What is the difference between bosons and fermions?", "Bosons have integer spin (0,1,2) and obey Bose-Einstein statistics — multiple bosons can occupy the same quantum state. Fermions have half-integer spin (1/2, 3/2) and obey Fermi-Dirac statistics and the Pauli exclusion principle — no two fermions can occupy the same state"),
    ("What is the Higgs boson?", "An elementary particle in the Standard Model associated with the Higgs field, which gives other particles mass via the Higgs mechanism. Discovered at CERN in 2012. Peter Higgs and Francois Englert won the Nobel Prize for the theory"),
    ("What is general relativity?", "Einstein's theory of gravity published in 1915: gravity is not a force but the curvature of spacetime caused by mass and energy. The field equations are G_mu_nu + Lambda*g_mu_nu = (8*pi*G/c^4)*T_mu_nu. Predicts black holes, gravitational waves, and time dilation"),
    ("What is general relativity?", "Einstein's 1915 theory: gravity = curvature of spacetime. Mass tells spacetime how to curve, curved spacetime tells mass how to move"),
    ("Explain quantum field theory", "A theoretical framework combining quantum mechanics with special relativity. Particles are excitations of underlying quantum fields. The Standard Model is a quantum field theory with gauge group SU(3)xSU(2)xU(1) describing electromagnetic, weak, and strong forces"),
    ("What is string theory?", "A theoretical framework where point-like particles are replaced by one-dimensional strings. Requires 10 or 11 dimensions. Aims to unify quantum mechanics and general relativity. No experimental evidence yet, but mathematically consistent"),
    ("What is the holographic principle?", "A conjecture that all information inside a volume of space can be encoded on its boundary surface. Inspired by black hole thermodynamics (Bekenstein-Hawking entropy S = A/4). The AdS/CFT correspondence is a concrete example"),
    ("Explain the Many-Worlds interpretation", "Hugh Everett's 1957 interpretation of quantum mechanics: all quantum possibilities branch into parallel universes. No wavefunction collapse occurs. Each measurement outcome exists in its own branch. Addresses the measurement problem without adding collapse or hidden variables"),
    ("What is a superconductor?", "A material that conducts electricity with zero electrical resistance below a critical temperature. Also exhibits the Meissner effect (expels magnetic fields). Types: Type-I (sudden transition, pure metals) and Type-II (gradual, allows partial flux penetration, high-Tc ceramics)"),

    # === Complex Math ===
    ("What is the Navier-Stokes existence and smoothness problem?", "One of 7 Millennium Prize Problems. Asks whether solutions to the Navier-Stokes equations (describing fluid flow) always exist and are smooth in 3D. Despite their physical importance, global regularity of 3D Navier-Stokes remains unproven. Clay Institute offers $1,000,000 for a proof"),
    ("What is the Birch and Swinnerton-Dyer conjecture?", "A Millennium Problem about elliptic curves. Conjectures that the rank of an elliptic curve (number of independent rational points) equals the order of zero of its L-function at s=1. Has deep implications for number theory and cryptography"),
    ("What is the Yang-Mills existence and mass gap problem?", "A Millennium Problem. Requires proving that quantum Yang-Mills theory exists in 4 dimensions and has a mass gap (lowest excited state has positive energy). The mass gap explains why the strong nuclear force has short range. Central to understanding quantum chromodynamics"),
    ("What is the Hodge conjecture?", "A Millennium Problem asking whether every Hodge class on a non-singular projective algebraic variety is a rational linear combination of cohomology classes of algebraic cycles. In simpler terms: can every nice topological shape be built from simpler algebraic pieces?"),
    ("What is Godel's incompleteness theorem?", "Kurt Godel's 1931 theorem: any sufficiently powerful formal system (capable of arithmetic) is either incomplete (there are true statements it cannot prove) or inconsistent (it proves contradictions). No formal system can prove all mathematical truths. This fundamentally limits the power of axiomatic mathematics"),
    ("What is Godel's incompleteness theorems?", "(1) Any consistent formal system strong enough for arithmetic cannot prove its own consistency. (2) There exist true arithmetic statements that cannot be proved within the system. Revolutionized logic and philosophy of mathematics"),
    ("What is the halting problem?", "Alan Turing's 1936 proof that no general algorithm can determine whether an arbitrary program will halt or run forever. Solved by diagonalization: assume H exists, construct a program that halts iff H says it doesn't halt, contradiction. Proves undecidability exists"),
    ("What is the P vs NP problem?", "The central unsolved problem of computer science: can every problem whose solution can be verified quickly (NP) also be solved quickly (P)? Most believe P != NP. A correct proof wins $1,000,000 from the Clay Institute. Implications for cryptography, optimization, and AI"),

    # === Hard Philosophy / AI ===
    ("What is the hard problem of consciousness?", "Philosopher David Chalmers' term: why and how do physical brain processes give rise to subjective experience (qualia)? Contrasted with 'easy problems' like explaining cognitive functions. No consensus solution exists. Approaches: materialism, dualism, panpsychism, idealism"),
    ("What is the Chinese room argument?", "John Searle's 1980 thought experiment against strong AI: a person following rules to manipulate Chinese symbols (without understanding Chinese) simulates understanding but has none. Argument: syntax alone is insufficient for semantics. Computers process symbols but don't understand meaning"),
    ("What is the simulation hypothesis?", "The hypothesis that reality is a computer simulation. Nick Bostrom's trilemma: either (1) civilizations don't reach simulation-creating capability, (2) they choose not to run simulations, or (3) we are almost certainly in a simulation. No empirical evidence, but philosophically provocative"),
    ("What is Roko's basilisk?", "A thought experiment about an AI that could retroactively punish those who didn't help create it. Critics argue that even discussing it increases risk. Controversial on LessWrong. Many consider it a flawed argument due to acausal trade issues"),
    ("What is the paperclip maximizer?", "Nick Bostrom's thought experiment about an AI whose only goal is maximizing paperclip production. Without proper value alignment, it could convert the entire Earth (and beyond) into paperclips, destroying humanity. Illustrates the risks of goal misalignment in AI"),

    # === Hard Technology ===
    ("How does quantum computing work?", "Uses quantum bits (qubits) that exploit superposition (exist in multiple states simultaneously) and entanglement (correlated states across distance). Quantum gates manipulate qubits. Algorithms like Shor's (factoring) and Grover's (search) achieve exponential or quadratic speedups over classical computers"),
    ("What is Shor's algorithm?", "Peter Shor's 1994 quantum algorithm for integer factorization in polynomial time (O((log N)^3)). Breaks RSA encryption by factoring large numbers exponentially faster than classical algorithms. Requires thousands of logical qubits. One of the main motivations for building quantum computers"),
    ("What is a neural tangent kernel?", "A kernel function that describes the training dynamics of infinitely-wide neural networks under gradient descent. Shows that wide neural networks converge to a Gaussian process. The NTK remains constant during training in the infinite-width limit, simplifying analysis"),
    ("What is the transformer architecture in deep learning?", "The 'Attention Is All You Need' architecture (Vaswani et al. 2017). Core innovation: multi-head self-attention mechanism allowing each token to attend to all other tokens. Key components: positional encoding, multi-head attention, feed-forward layers, layer normalization. Foundation of GPT, BERT, and all modern LLMs"),
    ("How does backpropagation work?", "The algorithm for training neural networks using gradient descent. Forward pass: compute output. Backward pass: compute gradient of loss with respect to each weight via the chain rule. Update weights in direction that minimizes loss. Efficiently computes partial derivatives through all layers"),
    ("What is the difference between L1 and L2 regularization?", "L1 (Lasso): adds sum of absolute weights to loss, produces sparse models (some weights become zero), useful for feature selection. L2 (Ridge): adds sum of squared weights to loss, shrinks all weights non-zero, prevents overfitting. Elastic Net combines both"),

    # === Hard Biology / Medicine ===
    ("What is CRISPR-Cas9?", "A gene-editing tool derived from bacterial immune systems. Cas9 enzyme cuts DNA at a location specified by a guide RNA. Enables precise genome editing: knock out genes, insert new sequences, or correct mutations. Discovered by Emmanuelle Charpentier and Jennifer Doudna (Nobel 2020)"),
    ("How does mRNA vaccine technology work?", "Synthetic mRNA encoding a viral spike protein is delivered via lipid nanoparticles. Cells translate mRNA into spike protein, triggering an immune response. T-cells and B-cells develop memory. Advantages: rapid development, no live virus, easily modifiable for variants. Used in COVID-19 vaccines (Pfizer, Moderna)"),
    ("What is the prion hypothesis?", "Prions are misfolded proteins that cause neurodegenerative diseases (Creutzfeldt-Jakob, mad cow, kuru). They propagate by inducing normal proteins to misfold into the same abnormal shape. Controversial because it challenges the 'DNA → RNA → protein' central dogma — infectious agents without nucleic acids"),
    ("What are telomeres and their role in aging?", "Telomeres are protective caps at chromosome ends consisting of repeated TTAGGG sequences. They shorten with each cell division. When too short, cells enter senescence (Hayflick limit). Telomerase can extend telomeres but is inactive in most adult cells. Telomere shortening is a key mechanism of cellular aging"),

    # === Hard Physics ===
    ("What is the black hole information paradox?", "Stephen Hawking's 1976 paradox: black holes emit Hawking radiation and eventually evaporate. But Hawking radiation appears thermal, carrying no information about what fell in. This violates quantum mechanics' unitarity (information must be preserved). Resolution may involve holography, firewalls, or complementarity"),
    ("What is Hawking radiation?", "Stephen Hawking's 1974 prediction: black holes emit thermal radiation due to quantum effects near the event horizon. Virtual particle pairs form; one falls in, the other escapes. The black hole gradually loses mass and eventually evaporates. Temperature inversely proportional to mass: T = hbar*c^3/(8*pi*G*M*k_B)"),
    ("What is dark flow?", "A controversial observation by Kashlinsky et al. (2008) of galaxy clusters moving in a consistent direction at ~1000 km/s, not explained by known large-scale structure. May indicate gravitational pull from matter beyond the observable universe. Existence debated; could be a systematic effect in the data"),
    ("What is the cosmological constant problem?", "The huge discrepancy between the observed value of the cosmological constant (Lambda, dark energy density ~10^-47 GeV^4) and quantum field theory predictions (~10^74 GeV^4) — a 120 orders of magnitude mismatch. One of the biggest unsolved problems in physics. May require quantum gravity or anthropic reasoning"),
    ("What is spontaneous symmetry breaking?", "A mechanism where a system's ground state has less symmetry than the underlying theory. In particle physics: the Higgs field acquires a vacuum expectation value, breaking electroweak symmetry and giving W/Z bosons mass. In condensed matter: ferromagnetism breaks rotational symmetry below Curie temperature"),
]


class FactTable:
    def __init__(self):
        self._seed_to_fact: Dict[int, Dict[str, Any]] = {}
        self._question_to_seed: Dict[str, int] = {}
        self._domain_to_facts: Dict[str, List[str]] = {}
        self._hit_count = 0
        self._miss_count = 0
        self._build_index()

    def _build_index(self):
        for question, answer in FACT_DB:
            seed = _hash_to_seed(question)
            self._question_to_seed[question.lower().strip()] = seed
            domain = self._classify(question)
            self._seed_to_fact[seed] = {
                "question": question,
                "answer": answer,
                "domain": domain,
                "seed": seed,
            }
            if domain not in self._domain_to_facts:
                self._domain_to_facts[domain] = []
            self._domain_to_facts[domain].append(question)

    def _classify(self, question: str) -> str:
        q = question.lower()
        if any(w in q for w in ["math", "number", "prime", "pi", "phi", "golden", "square root", "fibonacci"]):
            return "mathematics"
        if any(w in q for w in ["capital", "country", "continent", "river", "ocean", "mountain", "desert", "city"]):
            return "geography"
        if any(w in q for w in ["physics", "gravity", "light", "quantum", "energy", "matter", "speed", "atom"]):
            return "physics"
        if any(w in q for w in ["water", "chemistry", "element", "acid", "base", "ph", "periodic", "molecule"]):
            return "chemistry"
        if any(w in q for w in ["dna", "rna", "cell", "protein", "evolution", "gene", "virus", "vaccine", "mitochondria"]):
            return "biology"
        if any(w in q for w in ["who wrote", "who painted", "who composed", "book", "author", "novel", "shakespeare"]):
            return "literature"
        if any(w in q for w in ["president", "war", "history", "revolution", "empire", "century", "cold war", "pyramid"]):
            return "history"
        if any(w in q for w in ["invent", "computer", "cpu", "ram", "html", "http", "algorithm", "binary", "byte"]):
            return "technology"
        if any(w in q for w in ["consciousness", "meaning of life", "philosophy", "socrates", "plato", "aristotle"]):
            return "philosophy"
        if any(w in q for w in ["sun", "star", "planet", "galaxy", "moon", "solar system", "earth", "mars", "jupiter"]):
            return "astronomy"
        if any(w in q for w in ["legs", "bones", "heart", "brain", "blood", "body", "human", "teeth", "eye"]):
            return "anatomy"
        if any(w in q for w in ["animal", "dog", "cat", "whale", "shark", "snake", "mammal", "bird", "bat"]):
            return "zoology"
        if any(w in q for w in ["song", "symphony", "music", "composer", "piano", "orchestra"]):
            return "music"
        if any(w in q for w in ["encrypt", "firewall", "virus", "hack", "malware", "phish", "ddos", "aes", "rsa", "security"]):
            return "cybersecurity"
        if any(w in q for w in ["nikto", "aknow", "creator", "created you", "built you", "who made"]):
            return "nikto"
        return "general"

    def lookup(self, question: str) -> Optional[Dict[str, Any]]:
        seed = _hash_to_seed(question)
        if seed in self._seed_to_fact:
            self._hit_count += 1
            return self._seed_to_fact[seed]
        q_lower = question.lower().strip()
        if q_lower in self._question_to_seed:
            s = self._question_to_seed[q_lower]
            self._hit_count += 1
            return self._seed_to_fact.get(s)
        self._miss_count += 1
        return None

    def lookup_by_seed(self, seed: int) -> Optional[Dict[str, Any]]:
        if seed in self._seed_to_fact:
            self._hit_count += 1
            return self._seed_to_fact[seed]
        self._miss_count += 1
        return None

    def knows_question(self, question: str) -> bool:
        return self.lookup(question) is not None

    def add_fact(self, question: str, answer: str, domain: str = "general"):
        seed = _hash_to_seed(question)
        self._question_to_seed[question.lower().strip()] = seed
        self._seed_to_fact[seed] = {
            "question": question,
            "answer": answer,
            "domain": domain or self._classify(question),
            "seed": seed,
        }
        d = domain or self._classify(question)
        if d not in self._domain_to_facts:
            self._domain_to_facts[d] = []
        self._domain_to_facts[d].append(question)

    def fact_count(self) -> int:
        return len(self._seed_to_fact)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_facts": self.fact_count(),
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_ratio": round(self._hit_count / max(self._hit_count + self._miss_count, 1), 3),
            "domains_covered": sorted(self._domain_to_facts.keys()),
        }

    def get_domain(self, question: str) -> str:
        entry = self.lookup(question)
        if entry:
            return entry.get("domain", "general")
        return self._classify(question)

    def save(self) -> dict:
        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
        }

    def load(self, data: dict):
        self._hit_count = data.get("hits", 0)
        self._miss_count = data.get("misses", 0)
