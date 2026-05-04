import json
from collections import Counter

# Словарь, который сопоставляет значения, полученные при скрейпинге, с каноническими категориями
TYPE_MAPPING = {
    # категории, соответствующие "detached"
    'Detached': 'detached',
    'House': 'detached',        # если просто "House" – считаем его как detached (можно изменить по необходимости)
    'Mews': 'detached',         # иногда мьюс – отдельные домики
    
    # категории, соответствующие "semi‑detached"
    'Semi-Detached': 'semi‑detached',
    
    # категории, соответствующие "terraced"
    'Terraced': 'terraced',
    'End of Terrace': 'terraced',
    'Town House': 'terraced',
    
    # категории, соответствующие "flat"
    'Apartment': 'flat',
    'Flat': 'flat',
    'Studio': 'flat',
    'Maisonette': 'flat',
    'Penthouse': 'flat',
    'Flat Share': 'flat',
    'Serviced Apartments': 'flat',
    'House Share': 'flat',
    'Duplex': 'flat',
    
    # Если в данных появятся эти типы – их можно добавить:
    # 'Bungalow': 'bungalow',
    # 'Student Halls': 'student halls',
    
    # Если тип не указан или не найден в маппинге – по умолчанию считаем flat
    'Not Specified': 'flat',
    # Например, Parking – не является жилой недвижимостью, поэтому можем его исключить (None)
    'Parking': None
}

def map_property_type(scraped_type):
    """
    По значению, полученному при скрейпинге, возвращает каноническую категорию.
    Если тип не найден в словаре, возвращаем 'flat' как значение по умолчанию.
    """
    return TYPE_MAPPING.get(scraped_type, 'flat')

def count_canonical_types(json_filename):
    # Загружаем данные из JSON-файла
    with open(json_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    canonical_counts = Counter()
    
    for item in data:
        # Предполагается, что у каждого объявления есть поле "property_type"
        scraped_type = item.get('property_type', 'Not Specified')
        canonical_category = map_property_type(scraped_type)
        if canonical_category is not None:
            canonical_counts[canonical_category] += 1
        else:
            # Если значение None (например, для Parking) – пропускаем
            continue
    return canonical_counts

def main():
    json_filename = 'scraped_properties.json'  # Замените на имя вашего файла
    counts = count_canonical_types(json_filename)
    
    # Для удобства выведем результаты по всем каноническим категориям (даже если их счетчик равен 0)
    canonical_categories = ['detached', 'semi‑detached', 'terraced', 'flat', 'bungalow', 'student halls']
    
    print("Количество объектов по каноническим типам недвижимости:")
    for category in canonical_categories:
        print(f"{category}: {counts.get(category, 0)}")

if __name__ == '__main__':
    main()
