// 行业分类常量定义
export const INDUSTRY_CATEGORIES = [
  { value: 'hospital', label: '医院' },
  { value: 'education', label: '教育' },
  { value: 'finance_insurance', label: '金融/保险' },
  { value: 'public_administration', label: '公共管理与社会组织' },
  { value: 'government_military', label: '机关事业单位及部队' },
  { value: 'scientific_research', label: '科学研究、技术服务业和地质勘探业' },
  { value: 'information_technology', label: '信息传输、计算机服务、软件和技术服务业' },
  { value: 'international_organization', label: '国际性组织' },
  { value: 'water_environment', label: '水利、环境与公共设施管理行业' },
  { value: 'manufacturing', label: '制造业' },
  { value: 'construction', label: '建筑业' },
  { value: 'utilities', label: '电力，燃气及水的生产及供应业' },
  { value: 'transportation_logistics', label: '交通运输，仓储和邮政业' },
  { value: 'wholesale_retail', label: '批发和零售业' },
  { value: 'real_estate', label: '房地产业' },
  { value: 'leasing_business', label: '租赁及商业' },
  { value: 'tourism', label: '旅游业' },
  { value: 'culture_sports', label: '文化，体育和娱乐业' },
  { value: 'mining', label: '采掘业' },
  { value: 'hospitality_catering', label: '住宿和餐饮业' },
  { value: 'agriculture', label: '农业、林业、牧业、渔业' },
  { value: 'resident_services', label: '居民服务以及其他服务行业' },
  { value: 'import_export', label: '进出口贸易业' },
  { value: 'consulting_services', label: '律所、会计事务所等咨询' },
  { value: 'business_services', label: '工商服务业' },
  { value: 'temporary_worker', label: '临时工' },
  { value: 'retired', label: '退休' },
  { value: 'housewife', label: '家庭妇女' },
  { value: 'student', label: '学生' },
  { value: 'unemployed', label: '待业' },
  { value: 'other', label: '其他' }
];

// 获取所有分类选项
export const getCategoryOptions = () => INDUSTRY_CATEGORIES;

// 根据值获取标签
export const getCategoryLabel = (value: string): string => {
  const category = INDUSTRY_CATEGORIES.find(cat => cat.value === value);
  return category ? category.label : '未知分类';
};

// 根据标签获取值
export const getCategoryValue = (label: string): string => {
  const category = INDUSTRY_CATEGORIES.find(cat => cat.label === label);
  return category ? category.value : 'other';
};
