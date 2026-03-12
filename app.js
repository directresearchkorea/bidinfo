document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    // UI Elements
    const checkboxes = document.querySelectorAll('.custom-checkbox input');
    const searchInput = document.getElementById('search-input');
    const totalBidsEl = document.getElementById('total-bids');
    const updateTimeEl = document.getElementById('update-time');
    
    // Modal Elements
    const modal = document.getElementById('event-modal');
    const closeModal = document.getElementById('close-modal');
    
    // Set Current Time
    const now = new Date();
    updateTimeEl.textContent = now.toLocaleDateString('ko-KR') + ' ' + now.toLocaleTimeString('ko-KR', {hour: '2-digit', minute:'2-digit'});
    
    // Weather Fetch Logic (Sejong City)
    async function fetchWeather() {
        try {
            // Sejong City Approx. Lat/Lon
            const lat = 36.4800;
            const lon = 127.2890;
            const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`);
            const data = await res.json();
            
            if (data && data.current_weather) {
                const temp = Math.round(data.current_weather.temperature);
                const weathercode = data.current_weather.weathercode;
                
                document.getElementById('weather-temp').textContent = `${temp}°C`;
                
                let iconClass = 'fa-sun';
                if (weathercode === 0) iconClass = 'fa-sun';
                else if (weathercode >= 1 && weathercode <= 3) iconClass = 'fa-cloud-sun';
                else if (weathercode >= 45 && weathercode <= 48) iconClass = 'fa-smog';
                else if (weathercode >= 51 && weathercode <= 67) iconClass = 'fa-cloud-rain';
                else if (weathercode >= 71 && weathercode <= 82) iconClass = 'fa-snowflake';
                else iconClass = 'fa-cloud';
                
                document.getElementById('weather-icon').innerHTML = `<i class="fa-solid ${iconClass}"></i>`;
            }
        } catch (error) {
            console.error('Failed to fetch weather:', error);
            document.getElementById('weather-icon').innerHTML = '<i class="fa-solid fa-cloud-bolt"></i>';
            document.getElementById('weather-temp').textContent = 'Error';
        }
    }
    
    fetchWeather();
    
    // Filter Function
    function getActiveFilters() {
        const categories = Array.from(document.querySelectorAll('input[value="market"], input[value="consumer"], input[value="user"], input[value="social"], input[value="panel"], input[value="research"], input[value="sejong"]'))
            .filter(cb => cb.checked).map(cb => cb.value);
            
        const sources = Array.from(document.querySelectorAll('input[value="gov"], input[value="global"]'))
            .filter(cb => cb.checked).map(cb => cb.value);
            
        return { categories, sources };
    }
    
    // Helper: Map data from event_data.js format
    // Expected format: { title, organization, start (or deadline), category, source, url, description }
    let calendarEvents = [];
    if (typeof bidEvents !== 'undefined') {
        calendarEvents = bidEvents.map(event => {
            let color = '';
            if (event.category === 'market') color = 'var(--category-market)';
            else if (event.category === 'consumer') color = 'var(--category-consumer)';
            else if (event.category === 'user') color = 'var(--category-user)';
            else if (event.category === 'social') color = 'var(--category-social)';
            else if (event.category === 'panel') color = 'var(--category-panel)';
            else if (event.category === 'research') color = 'var(--category-research)';
            else if (event.category === 'sejong') color = 'var(--category-sejong)';
            else color = '#8b949e';
            
            return {
                id: event.id || Math.random().toString(36).substr(2, 9),
                title: event.title,
                start: event.deadline || event.start, // Use deadline for the calendar display date
                backgroundColor: color,
                extendedProps: {
                    organization: event.organization || '미상',
                    description: event.description || '상세 내용 없음',
                    url: event.url || '#',
                    category: event.category,
                    source: event.source
                }
            };
        });
    }

    // Initialize FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'ko',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listMonth'
        },
        buttonText: {
            today: '오늘',
            month: '월간',
            week: '주간',
            list: '목록'
        },
        height: '100%',
        events: function(info, successCallback, failureCallback) {
            const filters = getActiveFilters();
            const searchTerm = searchInput.value.toLowerCase().trim();
            
            const filteredEvents = calendarEvents.filter(event => {
                const c = event.extendedProps.category;
                const s = event.extendedProps.source;
                
                // Filter by category and source
                if (!filters.categories.includes(c)) return false;
                if (!filters.sources.includes(s)) return false;
                
                // Filter by search term
                if (searchTerm !== '') {
                    const searchStr = `${event.title} ${event.extendedProps.organization}`.toLowerCase();
                    if (!searchStr.includes(searchTerm)) return false;
                }
                
                return true;
            });
            
            // Update total stat
            totalBidsEl.textContent = filteredEvents.length;
            
            successCallback(filteredEvents);
        },
        eventClick: function(info) {
            info.jsEvent.preventDefault();
            const props = info.event.extendedProps;
            
            // Set Modal Data
            document.getElementById('modal-title').textContent = info.event.title;
            document.getElementById('modal-org').textContent = props.organization;
            
            // Format Deadline Display
            const d = info.event.start;
            const formattedDate = d ? d.toLocaleString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'}) : '미정';
            document.getElementById('modal-deadline').textContent = formattedDate;
            
            document.getElementById('modal-desc').textContent = props.description;
            
            // Setup Category Badge
            const badge = document.getElementById('modal-category');
            let catName = '입찰';
            if (props.category === 'market') {
                catName = 'Market Research';
                badge.style.backgroundColor = 'var(--category-market)';
                badge.style.color = '#fff';
            } else if (props.category === 'consumer') {
                catName = 'Consumer Research';
                badge.style.backgroundColor = 'var(--category-consumer)';
                badge.style.color = '#fff';
            } else if (props.category === 'user') {
                catName = 'User / UI·UX';
                badge.style.backgroundColor = 'var(--category-user)';
                badge.style.color = '#fff';
            } else if (props.category === 'social') {
                catName = 'Social Research';
                badge.style.backgroundColor = 'var(--category-social)';
                badge.style.color = '#fff';
            } else if (props.category === 'panel') {
                catName = 'Panel Research';
                badge.style.backgroundColor = 'var(--category-panel)';
                badge.style.color = '#fff';
            } else if (props.category === 'research') {
                catName = 'Research (조사)';
                badge.style.backgroundColor = 'var(--category-research)';
                badge.style.color = '#fff';
            } else if (props.category === 'sejong') {
                catName = 'Sejong Inst. (세종 공공기관)';
                badge.style.backgroundColor = 'var(--category-sejong)';
                badge.style.color = '#fff';
            }
            badge.textContent = catName;
            
            // Setup Link
            const linkBtn = document.getElementById('modal-link');
            if(props.url && props.url !== '#') {
                linkBtn.href = props.url;
                linkBtn.style.display = 'inline-flex';
            } else {
                linkBtn.style.display = 'none';
            }
            
            // Show modal
            modal.classList.remove('hidden');
        }
    });

    calendar.render();

    // Event Listeners for Filters
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => calendar.refetchEvents());
    });
    
    // Search functionality with debounce
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            calendar.refetchEvents();
        }, 300);
    });

    // Close Modal logic
    closeModal.addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // Close on click outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
    
    // Refresh Data mock
    document.getElementById('refresh-btn').addEventListener('click', () => {
        const btn = document.getElementById('refresh-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 수집 중...';
        btn.disabled = true;
        
        // Mock fetch delay
        setTimeout(() => {
            btn.innerHTML = '<i class="fa-solid fa-rotate-right"></i> 데이터 최신화';
            btn.disabled = false;
            
            const now = new Date();
            updateTimeEl.textContent = now.toLocaleDateString('ko-KR') + ' ' + now.toLocaleTimeString('ko-KR', {hour: '2-digit', minute:'2-digit'});
            
            calendar.refetchEvents();
            // In a real app we would fetch the JSON or trigger the python script endpoint
            alert("알림: 최신 데이터는 Python 에이전트 스크립트(오케스트레이터)를 통해 업데이트 됩니다.");
        }, 1500);
    });
    
    // Initial fetch stat update
    totalBidsEl.textContent = calendarEvents.length;
});
