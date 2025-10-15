from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from .emails import send_session_note_notification
from .models import Dupla, Program, Session, User
from .permissions import IsAdmin, IsDuplaParticipantOrAdmin
from .serializers import (
    AuthTokenSerializer,
    DuplaSerializer,
    ProgramAssignmentSerializer,
    ProgramSerializer,
    SessionSerializer,
    UserSerializer,
)
from .services import generate_ai_session_summary


class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class ObtainAuthTokenView(generics.GenericAPIView):
    serializer_class = AuthTokenSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'role': user.role})


class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all().prefetch_related('mentors', 'mentees')
    serializer_class = ProgramSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign(self, request, pk=None):
        program = self.get_object()
        serializer = ProgramAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mentor_ids = serializer.validated_data.get('mentor_ids', [])
        mentee_ids = serializer.validated_data.get('mentee_ids', [])

        if mentor_ids:
            mentors = User.objects.filter(id__in=mentor_ids, role=User.Role.MENTOR)
            program.mentors.add(*mentors)
        if mentee_ids:
            mentees = User.objects.filter(id__in=mentee_ids, role=User.Role.MENTEE)
            program.mentees.add(*mentees)
        return Response(ProgramSerializer(program).data)


class DuplaViewSet(viewsets.ModelViewSet):
    queryset = Dupla.objects.all().select_related('program', 'mentor', 'mentee')
    serializer_class = DuplaSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user
        if user.role == User.Role.MENTOR:
            queryset = queryset.filter(mentor=user)
        elif user.role == User.Role.MENTEE:
            queryset = queryset.filter(mentee=user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all().select_related('dupla', 'dupla__mentor', 'dupla__mentee')
    serializer_class = SessionSerializer
    permission_classes = [IsDuplaParticipantOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.MENTOR:
            queryset = queryset.filter(dupla__mentor=user)
        elif user.role == User.Role.MENTEE:
            queryset = queryset.filter(dupla__mentee=user)
        return queryset

    def perform_create(self, serializer):
        session = serializer.save()
        send_session_note_notification(session)

    def perform_update(self, serializer):
        session = serializer.save()
        send_session_note_notification(session)

    @action(detail=True, methods=['post'])
    def summarize(self, request, pk=None):
        session = self.get_object()
        summary = generate_ai_session_summary(session)
        return Response({'summary': summary})


class MentorAssignmentsView(generics.ListAPIView):
    serializer_class = DuplaSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role != User.Role.MENTOR:
            return Dupla.objects.none()
        return Dupla.objects.filter(mentor=user).select_related('program', 'mentee')


class MenteePlanView(generics.RetrieveAPIView):
    serializer_class = DuplaSerializer

    def get_object(self):
        user = self.request.user
        dupla = get_object_or_404(Dupla, pk=self.kwargs['pk'])
        if dupla.mentee != user and user.role != User.Role.ADMIN:
            raise PermissionDenied('You are not allowed to view this plan.')
        return dupla


class ExportDataView(generics.GenericAPIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        programs = Program.objects.count()
        duplas = Dupla.objects.count()
        sessions = Session.objects.count()
        payload = {
            'programs': programs,
            'duplas': duplas,
            'sessions': sessions,
        }
        return Response(payload)


class ImportDataView(generics.GenericAPIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        # Placeholder for CSV/Excel import implementation
        return Response({'status': 'import started'}, status=status.HTTP_202_ACCEPTED)


class BulkMatchView(generics.GenericAPIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        program_id = request.data.get('program_id')
        mentor_ids = request.data.get('mentor_ids', [])
        mentee_ids = request.data.get('mentee_ids', [])
        start_date = request.data.get('start_date')
        if not program_id or not start_date:
            return Response({'detail': 'program_id and start_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        program = get_object_or_404(Program, pk=program_id)
        created_duplas = []
        with transaction.atomic():
            for mentor_id, mentee_id in zip(mentor_ids, mentee_ids):
                mentor = get_object_or_404(User, pk=mentor_id, role=User.Role.MENTOR)
                mentee = get_object_or_404(User, pk=mentee_id, role=User.Role.MENTEE)
                program.mentors.add(mentor)
                program.mentees.add(mentee)
                dupla, _ = Dupla.objects.get_or_create(
                    program=program,
                    mentor=mentor,
                    mentee=mentee,
                    defaults={'start_date': start_date}
                )
                created_duplas.append(dupla)
        serializer = DuplaSerializer(created_duplas, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
