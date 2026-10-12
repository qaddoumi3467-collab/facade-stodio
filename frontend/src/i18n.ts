import { createContext, useContext } from 'react'

export type Lang = 'en' | 'ar'

const en = {
  'app.title': 'Facade Studio',
  'app.subtitle': 'Profile and system catalog',
  'lang.switch': 'العربية',

  'tab.systems': 'Systems',
  'tab.profiles': 'Profiles',
  'tab.glass': 'Glass',
  'tab.hardware': 'Hardware',

  'action.add': 'Add',
  'action.edit': 'Edit',
  'action.delete': 'Delete',
  'action.save': 'Save',
  'action.cancel': 'Cancel',
  'action.search': 'Search…',
  'action.calculate': 'Calculate',
  'confirm.delete': 'Delete this item?',

  'common.name': 'Name',
  'common.allSystems': 'All systems',
  'common.none': '—',
  'common.empty': 'Nothing here yet.',
  'common.loading': 'Loading…',
  'common.yes': 'Yes',
  'common.no': 'No',

  'field.code': 'Code',
  'field.article_no': 'Article no.',
  'field.name_en': 'Name (English)',
  'field.name_ar': 'Name (Arabic)',
  'field.manufacturer': 'Manufacturer',
  'field.description': 'Description',
  'field.thermal_break': 'Thermal break',
  'field.system_id': 'System',
  'field.role': 'Role',
  'field.width_mm': 'Width (mm)',
  'field.height_mm': 'Height (mm)',
  'field.weight_kg_per_m': 'Weight (kg/m)',
  'field.bar_length_mm': 'Bar length (mm)',
  'field.price_per_m': 'Price per m',
  'field.build_up': 'Build-up (e.g. 6-16-6)',
  'field.total_thickness_mm': 'Total thickness (mm)',
  'field.glass_thickness_mm': 'Glass only thickness (mm)',
  'field.u_value': 'U-value (W/m²K)',
  'field.price_per_m2': 'Price per m²',
  'field.category': 'Category',
  'field.unit': 'Unit',
  'field.price_per_unit': 'Price per unit',

  'role.frame': 'Frame',
  'role.sash': 'Sash',
  'role.mullion': 'Mullion',
  'role.transom': 'Transom',
  'role.glazing_bead': 'Glazing bead',
  'role.threshold': 'Threshold',
  'role.coupling': 'Coupling',
  'role.other': 'Other',

  'category.handle': 'Handle',
  'category.hinge': 'Hinge',
  'category.lock': 'Lock',
  'category.gasket': 'Gasket',
  'category.corner_cleat': 'Corner cleat',
  'category.roller': 'Roller',
  'category.accessory': 'Accessory',
  'category.other': 'Other',

  'unit.piece': 'Piece',
  'unit.set': 'Set',
  'unit.metre': 'Metre',

  'calc.profileTitle': 'Cut piece',
  'calc.glassTitle': 'Glass pane',
  'calc.length': 'Length (mm)',
  'calc.width': 'Width (mm)',
  'calc.height': 'Height (mm)',
  'calc.weight': 'Weight',
  'calc.area': 'Area',
  'calc.price': 'Price',
}

export type MessageKey = keyof typeof en

const ar: Record<MessageKey, string> = {
  'app.title': 'فاساد ستوديو',
  'app.subtitle': 'كتالوج القطاعات والأنظمة',
  'lang.switch': 'English',

  'tab.systems': 'الأنظمة',
  'tab.profiles': 'القطاعات',
  'tab.glass': 'الزجاج',
  'tab.hardware': 'الإكسسوارات',

  'action.add': 'إضافة',
  'action.edit': 'تعديل',
  'action.delete': 'حذف',
  'action.save': 'حفظ',
  'action.cancel': 'إلغاء',
  'action.search': 'بحث…',
  'action.calculate': 'احسب',
  'confirm.delete': 'هل تريد حذف هذا العنصر؟',

  'common.name': 'الاسم',
  'common.allSystems': 'كل الأنظمة',
  'common.none': '—',
  'common.empty': 'لا يوجد شيء بعد.',
  'common.loading': 'جارٍ التحميل…',
  'common.yes': 'نعم',
  'common.no': 'لا',

  'field.code': 'الرمز',
  'field.article_no': 'رقم الصنف',
  'field.name_en': 'الاسم (إنجليزي)',
  'field.name_ar': 'الاسم (عربي)',
  'field.manufacturer': 'الشركة المصنعة',
  'field.description': 'الوصف',
  'field.thermal_break': 'عازل حراري',
  'field.system_id': 'النظام',
  'field.role': 'الوظيفة',
  'field.width_mm': 'العرض (مم)',
  'field.height_mm': 'الارتفاع (مم)',
  'field.weight_kg_per_m': 'الوزن (كغ/م)',
  'field.bar_length_mm': 'طول العود (مم)',
  'field.price_per_m': 'السعر للمتر',
  'field.build_up': 'التركيب (مثال ٦-١٦-٦)',
  'field.total_thickness_mm': 'السماكة الكلية (مم)',
  'field.glass_thickness_mm': 'سماكة الزجاج فقط (مم)',
  'field.u_value': 'معامل U (واط/م²·ك)',
  'field.price_per_m2': 'السعر للمتر المربع',
  'field.category': 'الفئة',
  'field.unit': 'الوحدة',
  'field.price_per_unit': 'سعر الوحدة',

  'role.frame': 'حلق',
  'role.sash': 'ضلفة',
  'role.mullion': 'قاطع عمودي',
  'role.transom': 'قاطع أفقي',
  'role.glazing_bead': 'كلبس زجاج',
  'role.threshold': 'عتبة',
  'role.coupling': 'وصلة',
  'role.other': 'أخرى',

  'category.handle': 'مقبض',
  'category.hinge': 'مفصلة',
  'category.lock': 'قفل',
  'category.gasket': 'جلدة',
  'category.corner_cleat': 'زاوية تجميع',
  'category.roller': 'عجل',
  'category.accessory': 'ملحق',
  'category.other': 'أخرى',

  'unit.piece': 'قطعة',
  'unit.set': 'طقم',
  'unit.metre': 'متر',

  'calc.profileTitle': 'قطعة مقصوصة',
  'calc.glassTitle': 'لوح زجاج',
  'calc.length': 'الطول (مم)',
  'calc.width': 'العرض (مم)',
  'calc.height': 'الارتفاع (مم)',
  'calc.weight': 'الوزن',
  'calc.area': 'المساحة',
  'calc.price': 'السعر',
}

export const messages: Record<Lang, Record<MessageKey, string>> = { en, ar }

export function translate(lang: Lang, key: string): string {
  return messages[lang][key as MessageKey] ?? key
}

export const LangContext = createContext<Lang>('en')

export function useT() {
  const lang = useContext(LangContext)
  return { lang, t: (key: string) => translate(lang, key) }
}
