
import ProjectDetail from './ProjectDetail';
import { projectService } from '@/services/projectService';

// 允许动态参数，不仅限于 generateStaticParams 返回的参数
export const dynamicParams = true;

export async function generateStaticParams() {
  // 在构建时，我们只预生成一些常见的项目ID
  // 新建的项目会通过 dynamicParams = true 动态处理
  return [
    { id: '1' },
    { id: '2' },
    { id: '3' },
    { id: '4' },
    { id: '5' },
    { id: '6' },
    { id: '7' },
    { id: '8' },
    { id: '9' },
    { id: '10' },
  ];
}

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProjectDetail projectId={id} />;
}
