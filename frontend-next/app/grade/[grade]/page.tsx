import StudentGrader from "@/components/StudentGrader";

interface GradePageProps {
  params: Promise<{
    grade: string;
  }>;
}

export default async function GradePage({
  params,
}: GradePageProps) {
  const { grade } = await params;

  return (
    <StudentGrader
      grade={grade.toUpperCase()}
    />
  );
}